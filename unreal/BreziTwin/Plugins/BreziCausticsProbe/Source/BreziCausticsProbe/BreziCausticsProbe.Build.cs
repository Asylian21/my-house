using UnrealBuildTool;
using System.IO;
public class BreziCausticsProbe : ModuleRules
{
    public BreziCausticsProbe(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        // Ordinary installed engines remain dormant; the requested diagnostic fails explicitly at runtime.
        string FloorHeader = Path.Combine(EngineDirectory, "Source", "Runtime", "Renderer", "Public", "FloorCausticsRendering.h");
        bool HasFloorApi = File.Exists(FloorHeader);
        if (HasFloorApi && System.Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(FloorHeader))).ToLowerInvariant()
            != "0db646fb2813cd4ba7f7d03c921822bc55b9992a836c4904368c71386d9c8c52")
            throw new BuildException("Unreviewed FloorCausticsRendering public API bytes");
        PrivateDefinitions.Add("BREZI_HAS_FLOOR_CAUSTICS_API=" + (HasFloorApi ? "1" : "0"));
        PrivateDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "Projects", "Json", "RenderCore", "Renderer", "RHI" });
        RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Resources", "floor-provider-diagnostic.json"), StagedFileType.NonUFS);
        RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Resources", "transport-provider.json"), StagedFileType.NonUFS);
        RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Resources", "delivery-provider.json"), StagedFileType.NonUFS);
        RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Resources", "transport-scene-binding.json"), StagedFileType.NonUFS);
        if (Target.bBuildEditor) PrivateDependencyModuleNames.AddRange(new[] { "MeshDescription", "StaticMeshDescription" });
        RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Resources", "receiver-contract.json"), StagedFileType.NonUFS);
        RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Resources", "active-water-binding.json"), StagedFileType.NonUFS);
        RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Resources", "solar-visibility-cases.json"), StagedFileType.NonUFS);
    }
}
