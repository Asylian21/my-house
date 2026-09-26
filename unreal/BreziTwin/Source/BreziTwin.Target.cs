using UnrealBuildTool;
using System.Collections.Generic;

public class BreziTwinTarget : TargetRules
{
    public BreziTwinTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
        ExtraModuleNames.Add("BreziTwin");
        if (Target.Platform == UnrealTargetPlatform.Mac)
        {
            // Each model-refresh configuration has its own isolated project. Keep
            // the app/entry-point name stable for package sealing and LaunchServices.
            // This monolithic Game links installed configuration-specific .o files
            // through their precompiled manifests; no engine compile defines change.
            // UBT still uses a configuration-specific Shipping/Test target receipt.
            UndecoratedConfiguration = Target.Configuration;
            // App-owned entry keeps the original GUI executable and sandbox.
            // Installed UE marks linker arguments as shared-environment-sensitive.
            // These app-owned entry and naming choices do not change engine defines.
            bOverrideBuildEnvironment = true;
            AdditionalLinkerArguments = "-Wl,-e,_BreziMain";
        }
    }
}
