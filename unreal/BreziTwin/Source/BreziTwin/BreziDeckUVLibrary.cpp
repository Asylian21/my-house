#include "BreziDeckUVLibrary.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

#if WITH_EDITOR
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "MeshDescription.h"
#include "StaticMeshAttributes.h"
#include "StaticMeshCompiler.h"
#include "Misc/SecureHash.h"
#include "PhysicsEngine/BodySetup.h"
#include "Serialization/MemoryWriter.h"
#include "UObject/MetaData.h"
#include "UObject/Package.h"
#include "UObject/UnrealType.h"
#endif

namespace
{
    FString Json(const TSharedRef<FJsonObject>& Report)
    {
        FString Result;
        FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Result));
        return Result;
    }

    FString Fail(const TSharedRef<FJsonObject>& Report, const FString& Error)
    {
        Report->SetStringField(TEXT("status"), TEXT("failed"));
        Report->SetStringField(TEXT("error"), Error);
        return Json(Report);
    }

#if WITH_EDITOR
    constexpr const TCHAR* Owner = TEXT("BreziDeckUV1-v1");
    constexpr const TCHAR* OwnerKey = TEXT("BreziDeckUV1Owner");
    constexpr const TCHAR* RecipeKey = TEXT("BreziDeckUV1RecipeSha256");
    constexpr const TCHAR* BaselineKey = TEXT("BreziDeckUV1BaselineSignature");
    constexpr const TCHAR* PayloadKey = TEXT("BreziDeckUV1PayloadSha1");
    struct FScope { const TCHAR* Id; const TCHAR* Source; int32 Triangles; };
    const FScope Scope[] = {
        {TEXT("DOM_01708"), TEXT("Záhradná terasa · aktívne 30,60 m² · D1 34,80 m² · doska 1.1_merged"), 936},
        {TEXT("DOM_01710"), TEXT("Terasa D1 · západné rameno krídla · 33,10 m² · doska 1.1_merged"), 852},
        {TEXT("DOM_01713"), TEXT("Terasa D1 · krytá terasa pod štítom · 16,45 m² · doska 1.1_merged"), 564},
        {TEXT("DOM_01719"), TEXT("Bazénová drevená terasa · 1 m pozdĺžne / 2 m za bazénom · doska 1.1_merged"), 816},
        {TEXT("DOM_01779"), TEXT("Poklop technologickej šachty · zateplený pochôdzny poklop"), 12},
    };

    bool Hex(const FString& Value, int32 Length)
    {
        if (Value.Len() != Length) return false;
        for (TCHAR C : Value) if (!((C >= '0' && C <= '9') || (C >= 'a' && C <= 'f'))) return false;
        return true;
    }

    FString Hash(const TArray<uint8>& Bytes)
    {
        uint8 Digest[20];
        FSHA1::HashBuffer(Bytes.GetData(), Bytes.Num(), Digest);
        return BytesToHex(Digest, UE_ARRAY_COUNT(Digest)).ToLower();
    }

    FString HashText(const FString& Value)
    {
        FTCHARToUTF8 UTF8(*Value);
        TArray<uint8> Bytes;
        Bytes.Append(reinterpret_cast<const uint8*>(UTF8.Get()), UTF8.Length());
        return Hash(Bytes);
    }

    // Entire source descriptor, including all element connectivity and attributes.
    // Only the appended per-vertex-instance UV1 channel is excluded. UV0 is retained.
    TArray<uint8> BaselineBytes(const FMeshDescription& Description)
    {
        FMeshDescription Copy(Description);
        FStaticMeshAttributes(Copy).GetVertexInstanceUVs().SetNumChannels(1);
        TArray<uint8> Bytes;
        FMemoryWriter Writer(Bytes, true);
        Copy.Serialize(Writer); // UE uses FNameAsStringProxyArchive internally.
        return Bytes;
    }

    TArray<uint8> UVBytes(const TArray<int32>& Ids, const TArray<FVector2f>& Values)
    {
        TArray<uint8> Bytes;
        FMemoryWriter Writer(Bytes, true);
        int32 Count = Ids.Num(); Writer << Count;
        for (int32 I = 0; I < Count; ++I)
        {
            int32 Id = Ids[I]; float U = Values[I].X, V = Values[I].Y;
            Writer << Id << U << V;
        }
        return Bytes;
    }

    bool PropertyText(UObject* Object, const TCHAR* Name, FString& Text, FString& Error)
    {
        const FProperty* Property = FindFProperty<FProperty>(Object->GetClass(), Name);
        if (!Property) { Error = FString(TEXT("Missing inspected native property: ")) + Name; return false; }
        FString Value;
        Property->ExportText_InContainer(0, Value, Object, nullptr, Object, PPF_None);
        Text += FString(Name) + TEXT("=") + Value + TEXT("\n");
        return true;
    }

    template<class T> void StructText(const TCHAR* Name, const T& Value, UStaticMesh* Mesh, FString& Text)
    {
        FString Export;
        T::StaticStruct()->ExportText(Export, &Value, nullptr, Mesh, PPF_None, nullptr);
        Text += FString(Name) + TEXT("=") + Export + TEXT("\n");
    }

    bool Configuration(UStaticMesh* Mesh, FString& Text, FString& Error)
    {
        Text = TEXT("BreziDeckConfiguration-v1\n");
        // Material UV density is rebuilt by UE, so capture slot identities rather than that derived cache.
        for (const FStaticMaterial& Slot : Mesh->GetStaticMaterials())
            Text += FString::Printf(TEXT("slot=%s|%s|%s\n"), *GetPathNameSafe(Slot.MaterialInterface),
                *Slot.MaterialSlotName.ToString(), *Slot.ImportedMaterialSlotName.ToString());
        StructText(TEXT("build"), Mesh->GetSourceModel(0).BuildSettings, Mesh, Text);
        StructText(TEXT("reduction"), Mesh->GetSourceModel(0).ReductionSettings, Mesh, Text);
        StructText(TEXT("nanite"), Mesh->GetNaniteSettings(), Mesh, Text);
        StructText(TEXT("screenSize"), Mesh->GetSourceModel(0).ScreenSize, Mesh, Text);
        Text += FString::Printf(TEXT("sourceModels=%d;renderLODs=%d;renderTriangles=%d\n"),
            Mesh->GetNumSourceModels(), Mesh->GetNumLODs(), Mesh->GetNumTriangles(0));
        for (const TCHAR* Key : {TEXT("NeverStream"), TEXT("bAllowCPUAccess"), TEXT("bSupportRayTracing"),
            TEXT("LODForCollision"), TEXT("bAutoComputeLODScreenSize"), TEXT("LightMapCoordinateIndex"),
            TEXT("LightMapResolution"), TEXT("bHasNavigationData"), TEXT("bSupportPhysicalMaterialMasks"),
            TEXT("ComplexCollisionMesh"), TEXT("SectionInfoMap"), TEXT("OriginalSectionInfoMap")})
            if (!PropertyText(Mesh, Key, Text, Error)) return false;
        UBodySetup* Body = Mesh->GetBodySetup();
        if (!Body) { Error = TEXT("BodySetup absent"); return false; }
        Text += TEXT("body=") + Body->GetPathName() + TEXT("\n");
        for (const TCHAR* Key : {TEXT("AggGeom"), TEXT("DefaultInstance"), TEXT("CollisionTraceFlag"),
            TEXT("bDoubleSidedGeometry"), TEXT("bMeshCollideAll"), TEXT("bNeverNeedsCookedCollisionData"),
            TEXT("bGenerateNonMirroredCollision"), TEXT("bGenerateMirroredCollision"), TEXT("bSharedCookedData"),
            TEXT("bSupportUVsAndFaceRemap"), TEXT("bSupportFaceRemapOnMeshBVH"), TEXT("bSupportVertexRemap"),
            TEXT("PhysMaterial"), TEXT("WalkableSlopeOverride"), TEXT("BuildScale3D")})
            if (!PropertyText(Body, Key, Text, Error)) return false;
        return true;
    }

    struct FState
    {
        FMeshDescription* Description = nullptr;
        FString ObjectId, ConfigurationText, Signature;
        TArray<uint8> Attributes;
        TArray<int32> Ids;
        TArray<FVector2f> ExistingUV1;
        int32 Channels = 0;
    };

    bool State(UStaticMesh* Mesh, FState& Out, FString& Error)
    {
        if (!IsInGameThread() || !Mesh || Mesh->IsCompiling())
        { Error = TEXT("Requires a valid noncompiling mesh on the editor game thread"); return false; }
        FMetaData& Metadata = Mesh->GetOutermost()->GetMetaData();
        const FString Id = Metadata.GetValue(Mesh, TEXT("source_object_id"));
        const FScope* Selected = nullptr;
        for (const FScope& Entry : Scope) if (Id == Entry.Id) { Selected = &Entry; break; }
        if (!Selected || Mesh->GetPathName() != FString::Printf(TEXT("/Game/Brezi/Geometry/brezi-twin/StaticMeshes/%s.%s"), *Id, *Id)
            || Metadata.GetValue(Mesh, TEXT("source_id")) != Selected->Source)
        { Error = TEXT("Mesh namespace or exact canonical source identity is outside the deck scope"); return false; }
        if (Mesh->GetNumSourceModels() != 1 || Mesh->GetNumLODs() != 1 || Mesh->IsHiResMeshDescriptionValid())
        { Error = TEXT("Requires exactly one ordinary source/render LOD and no alternate hi-res source"); return false; }
        Out.Description = Mesh->GetMeshDescription(0);
        if (!Out.Description || Out.Description->Triangles().Num() != Selected->Triangles)
        { Error = TEXT("Canonical source descriptor or triangle count differs"); return false; }
        if (Mesh->GetSourceModel(0).BuildSettings.bGenerateLightmapUVs)
        { Error = TEXT("Generated lightmap UVs could overwrite the derived channel"); return false; }
        const auto UVs = FStaticMeshConstAttributes(*Out.Description).GetVertexInstanceUVs();
        Out.Channels = UVs.GetNumChannels();
        if (Out.Channels != 1 && Out.Channels != 2)
        { Error = TEXT("Only UV0 or UV0 plus owned UV1 is permitted"); return false; }
        Out.ObjectId = Id;
        for (FVertexInstanceID Instance : Out.Description->VertexInstances().GetElementIDs()) Out.Ids.Add(Instance.GetValue());
        Out.Ids.Sort();
        if (Out.Ids.IsEmpty() || Out.Ids.Num() > 50000)
        { Error = TEXT("Invalid bounded vertex-instance count"); return false; }
        if (!Configuration(Mesh, Out.ConfigurationText, Error)) return false;
        Out.Attributes = BaselineBytes(*Out.Description);
        Out.Signature = HashText(Hash(Out.Attributes) + TEXT("\n") + Out.ConfigurationText);
        if (Out.Channels == 2)
        {
            for (int32 Instance : Out.Ids) Out.ExistingUV1.Add(UVs.Get(FVertexInstanceID(Instance), 1));
            if (Metadata.GetValue(Mesh, OwnerKey) != Owner || !Hex(Metadata.GetValue(Mesh, RecipeKey), 64)
                || Metadata.GetValue(Mesh, BaselineKey) != Out.Signature
                || Metadata.GetValue(Mesh, PayloadKey) != Hash(UVBytes(Out.Ids, Out.ExistingUV1)))
            { Error = TEXT("Existing UV1 is foreign, stale or does not match its recorded recipe payload"); return false; }
        }
        return true;
    }

    void Describe(const FState& Value, const TSharedRef<FJsonObject>& Report)
    {
        Report->SetStringField(TEXT("sourceObjectId"), Value.ObjectId);
        Report->SetStringField(TEXT("baselineSignature"), Value.Signature);
        Report->SetStringField(TEXT("attributeSignature"), Hash(Value.Attributes));
        Report->SetStringField(TEXT("configurationSignature"), HashText(Value.ConfigurationText));
        Report->SetStringField(TEXT("signatureAlgorithm"), TEXT("sha1-local-equality-v1-not-source-provenance"));
        Report->SetNumberField(TEXT("vertexInstanceCount"), Value.Ids.Num());
        Report->SetNumberField(TEXT("uvChannels"), Value.Channels);
        Report->SetStringField(TEXT("configurationSnapshot"), Value.ConfigurationText);
        Report->SetBoolField(TEXT("savedReloaded"), false);
        Report->SetBoolField(TEXT("sourcePositionsIndependentlyVerified"), false);
        Report->SetBoolField(TEXT("collisionTrianglesVerified"), false);
    }
#endif
}

FString UBreziDeckUVLibrary::InspectDeckMesh(UStaticMesh* Mesh)
{
    const TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
#if WITH_EDITOR
    FState Before; FString Error;
    if (!State(Mesh, Before, Error)) return Fail(Report, Error);
    Describe(Before, Report);
    Report->SetStringField(TEXT("status"), TEXT("deck-mesh-inspected"));
    return Json(Report);
#else
    return Fail(Report, TEXT("Editor-only operation"));
#endif
}

FString UBreziDeckUVLibrary::ApplyDeckUV1(UStaticMesh* Mesh, const TArray<int32>& VertexInstanceIds,
    const TArray<FVector2D>& UV1, const FString& ExpectedBaselineSignature, const FString& RecipeSha256)
{
    const TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
#if WITH_EDITOR
    FState Before; FString Error;
    if (!State(Mesh, Before, Error)) return Fail(Report, Error);
    Describe(Before, Report);
    if (!Hex(ExpectedBaselineSignature, 40) || ExpectedBaselineSignature != Before.Signature || !Hex(RecipeSha256, 64))
        return Fail(Report, TEXT("Baseline changed or recipe signature is invalid"));
    if (VertexInstanceIds != Before.Ids || UV1.Num() != Before.Ids.Num())
        return Fail(Report, TEXT("UV payload must cover every native vertex instance exactly once in ascending order"));
    TArray<FVector2f> Values;
    for (const FVector2D& UV : UV1)
    {
        if (!FMath::IsFinite(UV.X) || !FMath::IsFinite(UV.Y) || FMath::Abs(UV.X) > 64.0 || FMath::Abs(UV.Y) > 64.0)
            return Fail(Report, TEXT("UV values must be finite and within the bounded deck recipe range [-64,64]"));
        Values.Add(FVector2f(UV));
    }
    const TArray<uint8> Payload = UVBytes(VertexInstanceIds, Values);
    FMetaData& Metadata = Mesh->GetOutermost()->GetMetaData();
    if (Before.Channels == 2)
    {
        if (Metadata.GetValue(Mesh, RecipeKey) != RecipeSha256 || UVBytes(Before.Ids, Before.ExistingUV1) != Payload)
            return Fail(Report, TEXT("Existing owned UV1 differs; reimport a verified UV0 source before changing the recipe"));
        Report->SetStringField(TEXT("status"), TEXT("deck-uv1-already-current"));
        Report->SetStringField(TEXT("recipeSha256"), RecipeSha256);
        Report->SetStringField(TEXT("uv1PayloadSha1"), Hash(Payload));
        Report->SetBoolField(TEXT("attributesPreserved"), true);
        Report->SetBoolField(TEXT("configurationPreserved"), true);
        Report->SetBoolField(TEXT("uv1Float32Exact"), true);
        Report->SetBoolField(TEXT("mutated"), false);
        Report->SetBoolField(TEXT("assetSaveAllowed"), true);
        return Json(Report);
    }
    // Refuse partially recorded or foreign marker sets, even when channel1 is absent.
    // Complete own markers can survive an Interchange UV0 reimport; only these four are replaced.
    const FString RecordedOwner = Metadata.GetValue(Mesh, OwnerKey);
    const bool bAnyMarkers = !RecordedOwner.IsEmpty() || !Metadata.GetValue(Mesh, RecipeKey).IsEmpty()
        || !Metadata.GetValue(Mesh, BaselineKey).IsEmpty() || !Metadata.GetValue(Mesh, PayloadKey).IsEmpty();
    if (bAnyMarkers && (RecordedOwner != Owner || !Hex(Metadata.GetValue(Mesh, RecipeKey), 64)
        || !Hex(Metadata.GetValue(Mesh, BaselineKey), 40) || !Hex(Metadata.GetValue(Mesh, PayloadKey), 40)))
        return Fail(Report, TEXT("Partial or foreign UV1 ownership markers"));
    FMeshDescription Original(*Before.Description);
    Mesh->Modify();
    auto UVs = FStaticMeshAttributes(*Before.Description).GetVertexInstanceUVs();
    UVs.SetNumChannels(2); // Do not insert: existing UV0 and lightmap indices remain in place.
    for (int32 I = 0; I < Before.Ids.Num(); ++I) UVs.Set(FVertexInstanceID(Before.Ids[I]), 1, Values[I]);
    Mesh->CommitMeshDescription(0);
    Mesh->PostEditChange(); // One standard editor rebuild, retaining the current build/Nanite policy.
    TArray<UStaticMesh*> Pending = {Mesh};
    FStaticMeshCompilingManager::Get().FinishCompilation(Pending);
    FMeshDescription* After = Mesh->GetMeshDescription(0);
    FString AfterConfiguration;
    const bool bConfiguration = Configuration(Mesh, AfterConfiguration, Error) && AfterConfiguration == Before.ConfigurationText;
    const bool bAttributes = After && BaselineBytes(*After) == Before.Attributes;
    bool bUVExact = After && FStaticMeshConstAttributes(*After).GetVertexInstanceUVs().GetNumChannels() == 2;
    TArray<FVector2f> Observed;
    if (bUVExact)
    {
        const auto CurrentUVs = FStaticMeshConstAttributes(*After).GetVertexInstanceUVs();
        for (int32 Id : Before.Ids)
        {
            if (!After->IsVertexInstanceValid(FVertexInstanceID(Id))) { bUVExact = false; break; }
            Observed.Add(CurrentUVs.Get(FVertexInstanceID(Id), 1));
        }
        bUVExact = bUVExact && UVBytes(Before.Ids, Observed) == Payload;
    }
    Report->SetBoolField(TEXT("attributesPreserved"), bAttributes);
    Report->SetBoolField(TEXT("configurationPreserved"), bConfiguration);
    Report->SetBoolField(TEXT("uv1Float32Exact"), bUVExact);
    Report->SetStringField(TEXT("afterConfigurationSignature"), HashText(AfterConfiguration));
    Report->SetStringField(TEXT("afterAttributeSignature"), After ? Hash(BaselineBytes(*After)) : TEXT("missing"));
    if (!bAttributes || !bConfiguration || !bUVExact || !Mesh->GetBodySetup()
        || Mesh->GetBodySetup()->bFailedToCreatePhysicsMeshes)
    {
        // No save occurs here. Restore the original source and rebuild; never claim config rollback without readback.
        Mesh->CreateMeshDescription(0, MoveTemp(Original));
        Mesh->CommitMeshDescription(0);
        Mesh->PostEditChange();
        FStaticMeshCompilingManager::Get().FinishCompilation(Pending);
        FState Restored; FString RestoreError;
        const bool bRestored = State(Mesh, Restored, RestoreError) && Restored.Signature == Before.Signature && Restored.Channels == 1;
        Report->SetBoolField(TEXT("sourceRollbackVerified"), bRestored);
        Report->SetBoolField(TEXT("assetSaveAllowed"), false);
        return Fail(Report, TEXT("Post-build preservation/readback failed; source rollback attempted, caller must abort without saving"));
    }
    Metadata.SetValue(Mesh, OwnerKey, Owner);
    Metadata.SetValue(Mesh, RecipeKey, *RecipeSha256);
    Metadata.SetValue(Mesh, BaselineKey, *Before.Signature);
    Metadata.SetValue(Mesh, PayloadKey, *Hash(Payload));
    Mesh->MarkPackageDirty();
    Report->SetNumberField(TEXT("uvChannels"), 2);
    Report->SetStringField(TEXT("recipeSha256"), RecipeSha256);
    Report->SetStringField(TEXT("uv1PayloadSha1"), Hash(Payload));
    Report->SetStringField(TEXT("status"), TEXT("deck-uv1-applied"));
    Report->SetBoolField(TEXT("mutated"), true);
    Report->SetBoolField(TEXT("assetSaveAllowed"), true);
    return Json(Report);
#else
    return Fail(Report, TEXT("Editor-only operation"));
#endif
}
