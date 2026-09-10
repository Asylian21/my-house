#include "BreziAXInitializer.h"
#include "BuildSettings.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Mac/CocoaThread.h"
#include "Mac/MacApplication.h"
#include "Misc/CommandLine.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Runtime/Launch/Resources/Version.h"
#if WITH_ACCESSIBILITY
#include "Mac/Accessibility/MacAccessibilityElement.h"
#include "Mac/Accessibility/MacAccessibilityManager.h"
#endif
#include <atomic>
#include <cstring>
#import <objc/runtime.h>

#if WITH_ACCESSIBILITY
namespace
{
    // All state touched by +load is constant-initialized. Do not call Slate,
    // logging, engine singletons, allocators or Cocoa dispatch queues in +load.
    std::atomic<bool> Stopping{false};
    std::atomic<uint64> Queued{0}, Applied{0}, MissingWidget{0}, MissingCache{0}, StaleGeneration{0}, ShutdownDrops{0}, Outstanding{0};
    uint64 NextGeneration = 0; // Main thread only.
    char GenerationKey;
    IMP OriginalInitializer = nullptr;
    IMP SafeInitializer = nullptr;
    Ivar CachedRoleIvar = nullptr;
    bool bEarlyInstalled = false;
    const char* EarlyFailure = "load-hook-not-run";
    std::atomic<bool> bStressRequested{false};
    bool bStressFinished = false;
    bool bStressPassed = false;
    std::atomic<uint64> StressMissingDrops{0};
    std::atomic<uint64> StressGenerationDrops{0};
    constexpr int32 StressCount = 16;

    struct FInitialValues
    {
        FString Label;
        FString Help;
        FVariant Value;
        AccessibleWidgetId Parent = IAccessibleWidget::InvalidAccessibleWidgetId;
        AccessibleWidgetId Window = IAccessibleWidget::InvalidAccessibleWidgetId;
        EAccessibleWidgetType Type = EAccessibleWidgetType::Unknown;
        bool bReadOnly = false;
        bool bPassword = false;
    };

    bool SupportedEngineConstants()
    {
        // These exported BuildSettings functions return compile-time constants;
        // unlike FEngineVersion::Current they do not initialize a lazy singleton.
        return ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 8 && ENGINE_PATCH_VERSION == 2
            && BuildSettings::GetEngineVersionMajor() == 5 && BuildSettings::GetEngineVersionMinor() == 8
            && BuildSettings::GetEngineVersionHotfix() == 2 && BuildSettings::GetCurrentChangelist() == 56702186
            && !BuildSettings::IsLicenseeVersion();
    }

    bool HasType(Method MethodToCheck, unsigned int Index, const char* Expected)
    {
        char Type[64] = {};
        method_getArgumentType(MethodToCheck, Index, Type, sizeof(Type));
        return std::strcmp(Type, Expected) == 0;
    }

    bool HasInitializerSignature(Method MethodToCheck)
    {
        if (!MethodToCheck || method_getNumberOfArguments(MethodToCheck) != 3) return false;
        char ReturnType[64] = {};
        method_getReturnType(MethodToCheck, ReturnType, sizeof(ReturnType));
        return std::strcmp(ReturnType, @encode(id)) == 0 && HasType(MethodToCheck, 0, @encode(id))
            && HasType(MethodToCheck, 1, @encode(SEL)) && HasType(MethodToCheck, 2, @encode(AccessibleWidgetId));
    }

    bool HasExpectedLayout(Class ElementClass)
    {
        if (!ElementClass || class_getSuperclass(ElementClass) != objc_getClass("NSAccessibilityElement")) return false;
        Ivar Children = class_getInstanceVariable(ElementClass, "_AccessibilityChildren");
        Ivar Role = class_getInstanceVariable(ElementClass, "_AccessibilityRole");
        Ivar Id = class_getInstanceVariable(ElementClass, "Id");
        Ivar Parent = class_getInstanceVariable(ElementClass, "ParentId");
        Ivar Window = class_getInstanceVariable(ElementClass, "OwningWindowId");
        if (!Children || !Role || !Id || !Parent || !Window) return false;
        const size_t BaseSize = class_getInstanceSize(class_getSuperclass(ElementClass));
        const size_t FullSize = class_getInstanceSize(ElementClass);
        return ivar_getTypeEncoding(Children)[0] == '@' && ivar_getTypeEncoding(Role)[0] == '@'
            && std::strcmp(ivar_getTypeEncoding(Id), @encode(AccessibleWidgetId)) == 0
            && std::strcmp(ivar_getTypeEncoding(Parent), @encode(AccessibleWidgetId)) == 0
            && std::strcmp(ivar_getTypeEncoding(Window), @encode(AccessibleWidgetId)) == 0
            && static_cast<size_t>(ivar_getOffset(Children)) >= BaseSize
            && ivar_getOffset(Role) == ivar_getOffset(Children) + sizeof(id)
            && ivar_getOffset(Id) >= ivar_getOffset(Role) + sizeof(id)
            && ivar_getOffset(Parent) == ivar_getOffset(Id) + sizeof(AccessibleWidgetId)
            && ivar_getOffset(Window) == ivar_getOffset(Parent) + sizeof(AccessibleWidgetId)
            && static_cast<size_t>(ivar_getOffset(Window)) + sizeof(AccessibleWidgetId) <= FullSize;
    }

    uint64 Generation(FMacAccessibilityElement* Element)
    {
        check([NSThread isMainThread]);
        return [(NSNumber*)objc_getAssociatedObject(Element, &GenerationKey) unsignedLongLongValue];
    }

    void QueueInitialValues(AccessibleWidgetId Id, uint64 GenerationId);
    void ApplyInitialValues(AccessibleWidgetId Id, uint64 GenerationId, const FInitialValues& Values);
}

// Installed ApplicationCore hides its private ivar offset symbols from the
// Editor dylib linker. The one cached-role write therefore uses public ObjC
// runtime reflection, guarded by the exact UE build, class layout and object
// encoding above. This is an engine ivar, not an Apple private API. No dealloc
// override, blanket release interception or engine binary edit is involved.
@interface FMacAccessibilityElement (BreziInitializerRepair)
- (id)brezi_safeInitWithId:(AccessibleWidgetId)Id;
- (void)brezi_applyInitialValues:(const FInitialValues&)Values;
@end

@implementation FMacAccessibilityElement (BreziInitializerRepair)
+ (void)load
{
    if (!SupportedEngineConstants()) { EarlyFailure = "unsupported-engine-build"; return; }
    Class ElementClass = objc_getClass("FMacAccessibilityElement");
    Method Original = class_getInstanceMethod(ElementClass, @selector(initWithId:));
    Method Replacement = class_getInstanceMethod(ElementClass, @selector(brezi_safeInitWithId:));
    if (!HasExpectedLayout(ElementClass) || !HasInitializerSignature(Original) || !HasInitializerSignature(Replacement))
    { EarlyFailure = "unexpected-class-layout-or-method-signature"; return; }
    OriginalInitializer = method_getImplementation(Original);
    SafeInitializer = method_getImplementation(Replacement);
    CachedRoleIvar = class_getInstanceVariable(ElementClass, "_AccessibilityRole");
    method_setImplementation(Original, SafeInitializer);
    bEarlyInstalled = method_getImplementation(Original) == SafeInitializer;
    EarlyFailure = bEarlyInstalled ? "none" : "method-installation-failed";
    // Permanent for this process. Restoring the unsafe IMP while callbacks are
    // pending, or unloading this game module live, is unsupported.
}

- (id)brezi_safeInitWithId:(AccessibleWidgetId)InId
{
    check([NSThread isMainThread]);
    self = [super init];
    if (self == nil) return nil;
    self.Id = InId;
    const uint64 GenerationId = ++NextGeneration;
    objc_setAssociatedObject(self, &GenerationKey, @(GenerationId), OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    // Crucially the dispatch helper is a free function: no nested block in an
    // Objective-C instance method can implicitly retain self on the game thread.
    QueueInitialValues(InId, GenerationId);
    return self;
}

- (void)brezi_applyInitialValues:(const FInitialValues&)Values
{
    check([NSThread isMainThread]);
    self.Label = Values.Label;
    self.Help = Values.Help;
    self.Value = Values.Value;
    self.LastCachedStringTime = FPlatformTime::Seconds();
    self.ParentId = Values.Parent;
    self.OwningWindowId = Values.Window;
    FMacAccessibilityManager* Manager = [FMacAccessibilityManager AccessibilityManager];
    // The receiver is already generation-checked. Preserve UE's ancestor lookup
    // semantics; any newly required ancestor uses this same safe initializer.
    if (Values.Parent != IAccessibleWidget::InvalidAccessibleWidgetId)
        self.accessibilityParent = [Manager GetAccessibilityElement:Values.Parent];
    if (Values.Window != IAccessibleWidget::InvalidAccessibleWidgetId)
        self.accessibilityWindow = [Manager GetAccessibilityElement:Values.Window];
    self.accessibilitySubrole = nil;
    NSAccessibilityRole Role = NSAccessibilityUnknownRole;
    switch (Values.Type)
    {
    case EAccessibleWidgetType::Button: Role = NSAccessibilityButtonRole; break;
    case EAccessibleWidgetType::CheckBox: Role = NSAccessibilityCheckBoxRole; break;
    case EAccessibleWidgetType::Image: Role = NSAccessibilityImageRole; break;
    case EAccessibleWidgetType::Slider: Role = NSAccessibilitySliderRole; break;
    case EAccessibleWidgetType::Text: Role = NSAccessibilityStaticTextRole; break;
    case EAccessibleWidgetType::TextEdit:
        Role = Values.bReadOnly ? NSAccessibilityStaticTextRole : NSAccessibilityTextFieldRole;
        if (!Values.bReadOnly && Values.bPassword) self.accessibilitySubrole = NSAccessibilitySecureTextFieldSubrole;
        break;
    case EAccessibleWidgetType::Window: Role = NSAccessibilityWindowRole; break;
    case EAccessibleWidgetType::Hyperlink:
        Role = NSAccessibilityLinkRole;
        self.accessibilitySubrole = NSAccessibilityTextLinkSubrole;
        break;
    case EAccessibleWidgetType::Layout: Role = NSAccessibilityLayoutAreaRole; break;
    case EAccessibleWidgetType::ComboBox: Role = NSAccessibilityComboBoxRole; break;
    default: break;
    }
    // UE's original MRC code assigns these immortal AppKit role constants.
    // Keep its cached role coherent with ExposeToVoiceOver's hide/show behavior.
    object_setIvar(self, CachedRoleIvar, Role);
    self.accessibilityRole = Role;
}
@end

namespace
{
    void ApplyInitialValues(AccessibleWidgetId Id, uint64 GenerationId, const FInitialValues& Values)
    {
        check([NSThread isMainThread]);
        if (Stopping.load()) { ++ShutdownDrops; return; }
        FMacAccessibilityManager* Manager = [FMacAccessibilityManager AccessibilityManager];
        if (![Manager AccessibilityElementExists:Id]) { ++MissingCache; return; }
        FMacAccessibilityElement* Element = [Manager GetAccessibilityElement:Id];
        if (Generation(Element) != GenerationId)
        {
            ++StaleGeneration;
            if (bStressRequested.load() && Id >= 2000000000 && Id < 2000000000 + StressCount) ++StressGenerationDrops;
            return;
        }
        [Element brezi_applyInitialValues:Values];
        ++Applied;
    }

    void QueueInitialValues(AccessibleWidgetId Id, uint64 GenerationId)
    {
        check([NSThread isMainThread]);
        if (Stopping.load()) { ++ShutdownDrops; return; }
        ++Queued;
        ++Outstanding;
        GameThreadCall(^{
            if (Stopping.load()) { ++ShutdownDrops; --Outstanding; return; }
            FInitialValues Values;
            {
                FMacApplication* Application = [FMacAccessibilityManager AccessibilityManager].MacApplication;
                const TSharedPtr<IAccessibleWidget> Widget = Application
                    ? Application->GetAccessibleMessageHandler()->GetAccessibleWidgetFromId(Id) : nullptr;
                if (!Widget.IsValid())
                {
                    ++MissingWidget;
                    if (bStressRequested && Id >= 2000000000 && Id < 2000000000 + StressCount) ++StressMissingDrops;
                    --Outstanding;
                    return;
                }
                Values.Label = Widget->GetWidgetName();
                Values.Help = Widget->GetHelpText();
                if (IAccessibleProperty* Property = Widget->AsProperty())
                {
                    Values.bReadOnly = Property->IsReadOnly();
                    Values.bPassword = Property->IsPassword();
                    if (!Values.bPassword) Values.Value = Property->GetValueAsVariant();
                }
                const TSharedPtr<IAccessibleWidget> Parent = Widget->GetParent();
                const TSharedPtr<IAccessibleWidget> Window = Widget->GetWindow();
                if (Parent.IsValid()) Values.Parent = Parent->GetId();
                if (Window.IsValid()) Values.Window = Window->GetId();
                Values.Type = Widget->GetWidgetType();
            } // All Slate widget shared pointers die on GT before the next block.
            MainThreadCall(^{
                ApplyInitialValues(Id, GenerationId, Values);
                --Outstanding;
            }, false);
        }, false);
    }
}
#endif

bool BreziAXInitializer::VerifyInstalled()
{
#if WITH_ACCESSIBILITY
    check(IsInGameThread());
    const FEngineVersion& Version = FEngineVersion::Current();
    const bool bValid = bEarlyInstalled && SupportedEngineConstants() && Version.GetMajor() == 5
        && Version.GetMinor() == 8 && Version.GetPatch() == 2 && Version.GetChangelist() == 56702186
        && method_getImplementation(class_getInstanceMethod(objc_getClass("FMacAccessibilityElement"), @selector(initWithId:))) == SafeInitializer;
    UE_LOG(LogTemp, Display, TEXT("BreziAXInitializer: installedAtLoad=%d exactBuild=%d reason=%s; ID/generation-only initializer, engine dealloc unchanged."),
        bEarlyInstalled, bValid, UTF8_TO_TCHAR(EarlyFailure));
    WriteReceipt("verified-after-engine-startup");
    return bValid;
#else
    return false;
#endif
}

void BreziAXInitializer::RunStressIfRequested()
{
#if WITH_ACCESSIBILITY
    check(IsInGameThread());
    if (bStressRequested || !FParse::Param(FCommandLine::Get(), TEXT("BreziAXInitStress"))) return;
    bStressRequested = true;
    FMacApplication* Application = [FMacAccessibilityManager AccessibilityManager].MacApplication;
    if (!Application || Stopping.load()) return;
    TArray<AccessibleWidgetId> Ids;
    for (int32 Index = 0; Index < StressCount; ++Index)
    {
        const AccessibleWidgetId Id = 2000000000 + Index;
        if (Application->GetAccessibleMessageHandler()->GetAccessibleWidgetFromId(Id).IsValid())
        { UE_LOG(LogTemp, Error, TEXT("BreziAXInitializer stress refused: candidate exists in Slate.")); return; }
        Ids.Add(Id);
    }
    __block bool bCacheWasClear = true;
    MainThreadCall(^{
        FMacAccessibilityManager* Manager = [FMacAccessibilityManager AccessibilityManager];
        for (const AccessibleWidgetId Id : Ids)
            if ([Manager AccessibilityElementExists:Id]) bCacheWasClear = false;
        if (!bCacheWasClear) return;
        for (const AccessibleWidgetId Id : Ids)
        {
            // These IDs cannot resolve in Slate. MainThreadCall(true) may pump
            // GT work during this loop, so no execution-order claim is made.
            @autoreleasepool
            {
                FMacAccessibilityElement* First = [Manager GetAccessibilityElement:Id];
                const uint64 OldGeneration = Generation(First);
                [Manager RemoveAccessibilityElement:Id];
                FMacAccessibilityElement* Second = [Manager GetAccessibilityElement:Id];
                FInitialValues SyntheticValues;
                ApplyInitialValues(Id, OldGeneration, SyntheticValues);
                check(Generation(Second) != OldGeneration);
                [Manager RemoveAccessibilityElement:Id];
            }
        }
    }, true);
    if (!bCacheWasClear) { UE_LOG(LogTemp, Error, TEXT("BreziAXInitializer stress refused: native candidate already exists.")); return; }
    // Dispatch queues are not FIFO fences; these are finite attempts over the
    // explicitly queued ID-only work. Do not assert a global queue is empty.
    for (int32 Attempt = 0; Attempt < 4 && StressMissingDrops.load() < StressCount * 2; ++Attempt)
    { ProcessGameThreadEvents(); MainThreadCall(^{}, true); }
    bStressFinished = true;
    bStressPassed = StressMissingDrops.load() == StressCount * 2
        && StressGenerationDrops.load() == StressCount;
    UE_LOG(LogTemp, Display, TEXT("BreziAXInitializer stress: passed=%d absentIds=%d staleGenerationDrops=%llu missingWidgetDrops=%llu; no system settings changed."),
        bStressPassed, StressCount, StressGenerationDrops.load(), StressMissingDrops.load());
    WriteReceipt("stress-finished");
#endif
}

void BreziAXInitializer::BeginShutdown()
{
#if WITH_ACCESSIBILITY
    Stopping.store(true);
#endif
}

void BreziAXInitializer::WriteReceipt(const char* Phase)
{
#if WITH_ACCESSIBILITY
    check(IsInGameThread());
    TSharedRef<FJsonObject> Receipt = MakeShared<FJsonObject>();
    Receipt->SetNumberField(TEXT("schemaVersion"), 1);
    Receipt->SetStringField(TEXT("phase"), UTF8_TO_TCHAR(Phase));
    Receipt->SetBoolField(TEXT("installedAtObjectiveCLoad"), bEarlyInstalled);
    Receipt->SetStringField(TEXT("engineGuard"), TEXT("5.8.2-56702186-non-licensee"));
    Receipt->SetStringField(TEXT("installationError"), UTF8_TO_TCHAR(EarlyFailure));
    Receipt->SetBoolField(TEXT("engineDeallocUnchanged"), true);
    Receipt->SetBoolField(TEXT("shutdownStarted"), Stopping.load());
    Receipt->SetNumberField(TEXT("queued"), Queued.load());
    Receipt->SetNumberField(TEXT("applied"), Applied.load());
    Receipt->SetNumberField(TEXT("missingWidgetDrops"), MissingWidget.load());
    Receipt->SetNumberField(TEXT("missingCacheDrops"), MissingCache.load());
    Receipt->SetNumberField(TEXT("staleGenerationDrops"), StaleGeneration.load());
    Receipt->SetNumberField(TEXT("shutdownDrops"), ShutdownDrops.load());
    Receipt->SetNumberField(TEXT("outstanding"), Outstanding.load());
    Receipt->SetBoolField(TEXT("stressRequested"), bStressRequested);
    Receipt->SetBoolField(TEXT("stressFinished"), bStressFinished);
    Receipt->SetBoolField(TEXT("stressPassed"), bStressPassed);
    Receipt->SetNumberField(TEXT("stressAbsentIdCount"), bStressRequested ? StressCount : 0);
    Receipt->SetNumberField(TEXT("stressMissingWidgetDrops"), StressMissingDrops.load());
    Receipt->SetNumberField(TEXT("stressStaleGenerationDrops"), StressGenerationDrops.load());
    Receipt->SetStringField(TEXT("scope"), TEXT("App-scoped initializer replacement. Captured blocks contain IDs/generation and copied values only; no self/native/Slate widget ownership crosses GT/Main. Stress proves absent-ID removal and stale-generation rejection; real AX interaction and shutdown still require native QA."));
    FString Text;
    FJsonSerializer::Serialize(Receipt, TJsonWriterFactory<>::Create(&Text));
    const FString Directory = FPaths::ProjectSavedDir() / TEXT("Diagnostics/AX");
    IFileManager::Get().MakeDirectory(*Directory, true);
    if (!FFileHelper::SaveStringToFile(Text, *(Directory / TEXT("initializer.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
        UE_LOG(LogTemp, Error, TEXT("BreziAXInitializer: could not write diagnostic receipt."));
#endif
}
