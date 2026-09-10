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
            // App-owned entry keeps the original GUI executable and sandbox.
            // Installed UE marks linker arguments as shared-environment-sensitive.
            // Only this monolithic app's final entry link changes; no engine defines.
            bOverrideBuildEnvironment = true;
            AdditionalLinkerArguments = "-Wl,-e,_BreziMain";
        }
    }
}
