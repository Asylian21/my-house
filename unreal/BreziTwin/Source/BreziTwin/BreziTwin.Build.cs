using UnrealBuildTool;

public class BreziTwin : ModuleRules
{
    public BreziTwin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "ApplicationCore", "Slate", "SlateCore", "Json", "RHI", "RenderCore", "ImageCore", "PhysicsCore", "BuildSettings" });
        if (Target.bBuildEditor) PrivateDependencyModuleNames.AddRange(new[] { "MeshDescription", "StaticMeshDescription" });
        if (Target.Platform == UnrealTargetPlatform.Mac) PublicFrameworks.Add("AppKit");
    }
}
