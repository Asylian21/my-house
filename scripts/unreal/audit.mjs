import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// Whitelist output fields; never persist raw system_profiler/plist/stderr data.
const exec = promisify(execFile);
const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const engine = process.env.UNREAL_ENGINE_ROOT ?? "/Users/Shared/Epic Games/UE_5.8";
const out = resolve(root, process.env.UNREAL_AUDIT_OUTPUT ?? "output/unreal/environment.json");
async function command(bin, args = []) {
  try {
    const { stdout } = await exec(bin, args, { timeout: 60000, maxBuffer: 4 * 1024 * 1024 });
    return { ok: true, stdout: stdout.trim() };
  } catch (error) {
    return { ok: false, code: typeof error.code === "number" ? error.code : "unavailable" };
  }
}
function json(result) {
  if (!result.ok) return null;
  try { return JSON.parse(result.stdout); } catch { return null; }
}
function version(result) { return result.ok ? result.stdout.split("\n")[0] : null; }
async function readJson(path) { try { return JSON.parse(await readFile(path, "utf8")); } catch { return null; } }
async function appVersion(path) {
  return version(await command("/usr/bin/plutil", ["-extract", "CFBundleShortVersionString", "raw", "-o", "-", `${path}/Contents/Info.plist`]));
}
const metalProbe = `import Metal
import Foundation
if let d = MTLCreateSystemDefaultDevice() {
 let values: [String: Any] = ["name": d.name, "supportsRaytracing": d.supportsRaytracing,
 "supportsRaytracingFromRender": d.supportsRaytracingFromRender,
 "apple8": d.supportsFamily(.apple8), "apple9": d.supportsFamily(.apple9),
 "recommendedMaxWorkingSetBytes": d.recommendedMaxWorkingSetSize]
 let data = try JSONSerialization.data(withJSONObject: values, options: [.sortedKeys])
 print(String(data: data, encoding: .utf8)!)
}`;
const [profile, os, osBuild, xcode, sdk, metal, metalLib, firstLaunch, disk, apfsPlist,
  brew, node, python, metalDevice, blenderVersion, epicVersion, build, appleSDK, editorFile] = await Promise.all([
  command("/usr/sbin/system_profiler", ["SPHardwareDataType", "SPDisplaysDataType", "-json"]),
  command("/usr/bin/sw_vers", ["-productVersion"]), command("/usr/bin/sw_vers", ["-buildVersion"]),
  command("/usr/bin/xcodebuild", ["-version"]), command("/usr/bin/xcrun", ["--sdk", "macosx", "--show-sdk-version"]),
  command("/usr/bin/xcrun", ["metal", "--version"]), command("/usr/bin/xcrun", ["--find", "metallib"]),
  command("/usr/bin/xcodebuild", ["-checkFirstLaunchStatus"]),
  command("/bin/df", ["-k", "/System/Volumes/Data"]), command("/usr/sbin/diskutil", ["apfs", "list", "-plist"]),
  command("/opt/homebrew/bin/brew", ["--version"]), command(process.execPath, ["--version"]),
  command("/usr/bin/python3", ["--version"]), command("/usr/bin/xcrun", ["swift", "-e", metalProbe]),
  appVersion("/Applications/Blender.app"), appVersion("/Applications/Epic Games Launcher.app"),
  readJson(`${engine}/Engine/Build/Build.version`), readJson(`${engine}/Engine/Config/Apple/Apple_SDK.json`),
  command("/usr/bin/file", [`${engine}/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor`]),
]);
const p = json(profile);
const hardware = p?.SPHardwareDataType?.[0] ?? {};
const displayEntries = (p?.SPDisplaysDataType ?? []).flatMap(gpu => (gpu.spdisplays_ndrvs ?? []).map(display => {
  const resolution = String(display._spdisplays_pixels ?? "").match(/(\d+)\s*x\s*(\d+)/);
  const width = resolution ? Number(resolution[1]) : null;
  const height = resolution ? Number(resolution[2]) : null;
  return { name: display._name ?? null, widthPixels: width, heightPixels: height,
    scaledResolution: display._spdisplays_resolution ?? null,
    builtIn: display.spdisplays_connection_type === "spdisplays_internal",
    online: display.spdisplays_online === "spdisplays_yes", supportsPhysicalUHD: width >= 3840 && height >= 2160 };
}));
let physicalAPFS = null;
if (apfsPlist.ok) {
  const parsed = await new Promise(resolveParsed => {
    const child = execFile("/usr/bin/plutil", ["-convert", "json", "-o", "-", "-"],
      { timeout: 10000, maxBuffer: 4 * 1024 * 1024 }, (error, stdout) => {
        try { resolveParsed(error ? null : JSON.parse(stdout)); } catch { resolveParsed(null); }
      });
    child.stdin.end(apfsPlist.stdout);
  });
  const container = parsed?.Containers?.find(c => c.Volumes?.some(v => v.Roles?.includes("Data")));
  if (container) physicalAPFS = { capacityBytes: container.CapacityCeiling,
    usedBytes: container.CapacityCeiling - container.CapacityFree, freeBytes: container.CapacityFree };
}
const df = disk.ok ? disk.stdout.split("\n").at(-1).trim().split(/\s+/) : [];
let metalSM6 = null;
try {
  const config = await readFile(`${engine}/Engine/Config/Mac/DataDrivenPlatformInfo.ini`, "utf8");
  const section = config.split("[ShaderPlatform METAL_SM6]")[1]?.split("\n[")[0];
  const keys = ["bSupportsLumenGI", "bSupportsRayTracing", "bSupportsRayTracingShaders", "bSupportsInlineRayTracing", "bSupportsPathTracing", "bSupportsNanite"];
  metalSM6 = Object.fromEntries(keys.map(key => [key, new RegExp(`^${key}\\s*=\\s*true\\s*$`, "m").test(section ?? "")]));
} catch { /* Missing engine is reported below. */ }
const report = {
  schemaVersion: 1, generatedAt: new Date().toISOString(),
  status: metal.ok && build ? "environment-audited-toolchain-present" : "environment-audited-prerequisites-missing",
  privacy: "Only allowlisted hardware, version, capacity and capability fields. No serials, hostnames, usernames, device IDs, accounts or raw command logs.",
  platform: { os: process.platform, architecture: process.arch, macOS: version(os), build: version(osBuild) },
  hardware: { model: hardware.machine_name ?? null, chip: hardware.chip_type ?? null,
    memory: hardware.physical_memory ?? null, cpuCores: Number(String(hardware.number_processors ?? "").match(/proc (\d+)/)?.[1]) || null,
    gpuCores: Number(p?.SPDisplaysDataType?.[0]?.sppci_cores) || null,
    metalFamily: p?.SPDisplaysDataType?.[0]?.spdisplays_mtlgpufamilysupport ?? null },
  displays: displayEntries, metalDevice: json(metalDevice),
  storage: { physicalAPFS, dataVolume: df.length > 3 ? { capacityBytes: Number(df[1]) * 1024,
    usedBytes: Number(df[2]) * 1024, freeBytes: Number(df[3]) * 1024 } : null },
  tools: { xcode: version(xcode), macOSSDK: version(sdk), xcodeFirstLaunchReady: firstLaunch.ok,
    metalCompiler: { available: metal.ok, version: version(metal) }, metallibAvailable: metalLib.ok,
    homebrew: version(brew), node: version(node), systemPython: version(python), blender: blenderVersion, epicLauncher: epicVersion },
  unreal: { installed: Boolean(build), version: build ? `${build.MajorVersion}.${build.MinorVersion}.${build.PatchVersion}` : null,
    changelist: build?.Changelist ?? null, editorArchitectures: editorFile.ok ? ["arm64", "x86_64"].filter(a => editorFile.stdout.includes(a)) : [],
    runUAT: existsSync(`${engine}/Engine/Build/BatchFiles/RunUAT.sh`),
    editorCommandlet: existsSync(`${engine}/Engine/Binaries/Mac/UnrealEditor-Cmd`),
    declaredXcode: appleSDK ? { main: appleSDK.MainVersion, min: appleSDK.MinVersion, max: appleSDK.MaxVersion } : null,
    metalSM6 },
  verification: { engineLaunchedByAudit: false, projectBuiltByAudit: false, native4KFrameRateMeasured: false,
    native4KDisplayAvailable: displayEntries.some(d => d.online && d.supportsPhysicalUHD),
    note: "GPU/config capability is not an Unreal runtime or visual-quality result." },
  nextPrerequisites: metal.ok ? [] : ["xcodebuild -downloadComponent MetalToolchain"],
  sources: [
    "https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes",
    "https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine?lang=en-US",
    "https://forums.unrealengine.com/t/unreal-engine-5-8-released/2729274",
  ],
  documentationCaveat: "The general macOS requirements HWRT row conflicts with 5.8 release notes and installed Metal SM6 source. 5.8 adds Mac Metal ray shaders/path tracing; notes request macOS >=26.4 for the driver fix. Confirm runtime separately.",
};
await mkdir(dirname(out), { recursive: true });
await writeFile(out, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report, null, 2));
