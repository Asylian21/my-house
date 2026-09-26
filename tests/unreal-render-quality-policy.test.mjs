import test from "node:test";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

test("render recipes, capability fallback, diagnostic ownership and persistence", {
  skip: process.platform !== "darwin" ? "Requires the macOS Unreal development toolchain" : false,
}, (t) => {
  const directory = mkdtempSync(resolve(tmpdir(), "brezi-quality-policy-"));
  try {
    for (const optimized of [false, true]) {
      const binary = resolve(directory, optimized ? "quality-optimized" : "quality-debug");
      execFileSync("xcrun", ["clang++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        ...(optimized ? ["-O2", "-DNDEBUG"] : []),
        resolve(import.meta.dirname, "unreal-render-quality-policy.cpp"), "-o", binary], { timeout: 30000 });
      t.diagnostic(execFileSync(binary, [], { encoding: "utf8", timeout: 5000 }).trim());
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
