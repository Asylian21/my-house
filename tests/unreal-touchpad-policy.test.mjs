import test from "node:test";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

test("native touchpad scaling preserves physical scale and fractional scroll", {
  skip: process.platform !== "darwin" ? "Requires the macOS Unreal development toolchain" : false,
}, (t) => {
  const directory = mkdtempSync(resolve(tmpdir(), "brezi-touchpad-policy-"));
  const root = resolve(import.meta.dirname, "..");
  try {
    for (const optimized of [false, true]) {
      const binary = resolve(directory, optimized ? "touchpad-optimized" : "touchpad-debug");
      execFileSync("xcrun", ["clang++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        ...(optimized ? ["-O2", "-DNDEBUG"] : []),
        "-I", resolve(root, "unreal/BreziTwin/Source/BreziTwin"),
        resolve(root, "tests/unreal-touchpad-policy.cpp"), "-o", binary], { timeout: 30000 });
      t.diagnostic(execFileSync(binary, [], { encoding: "utf8", timeout: 5000 }).trim());
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
