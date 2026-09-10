import test from "node:test";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

test("production camera fade policy preserves black cut ordering, retargeting and cancellation", {
  skip: process.platform !== "darwin" ? "Requires the macOS Unreal development toolchain" : false,
}, (t) => {
  const directory = mkdtempSync(resolve(tmpdir(), "brezi-camera-policy-"));
  const root = resolve(import.meta.dirname, "..");
  try {
    const binary = resolve(directory, "camera-policy");
    execFileSync("xcrun", ["clang++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
      "-I", resolve(root, "unreal/BreziTwin/Source/BreziTwin"),
      resolve(root, "tests/unreal-view-transition-policy.cpp"), "-o", binary], { timeout: 30000 });
    t.diagnostic(execFileSync(binary, [], { encoding: "utf8", timeout: 5000 }).trim());
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
