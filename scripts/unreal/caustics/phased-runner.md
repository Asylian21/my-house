# Reusable native phase runner

These tools are tracked-source owners under `scripts/unreal/caustics/`. Their canonical promotion and CPU checks did not run UE, a compiler, Xcode, cook, archive, or an app. Previously validated native delivery receipts remain separate evidence; this new orchestration has not yet been exercised end to end.

- `phase_runner.py`: explicit source snapshot, plan, read-only preflight, and separate graph/build/cook/archive execution.
- `native_process.py`: locally copied owned-process supervisor, retaining PID+start-time identity, initial baseline, descendant/active-PGID discovery, 120/900/600-second phase deadlines, 10-second post-exit drain, owned TERM→KILL cleanup and guarded direct-child fallback. Stdout goes to a file, so inherited pipes cannot hold the host open. Known unrelated compiler/Xcode work is retained in the baseline; candidate command/cwd conflicts and all live UE processes refuse launch.
- `accept_build.py`: clean build acceptance with matching source/graph/logs; Editor module mapping/BuildId and Renderer/plugin linkage; Game uses plain `nm` and requires actual `t/T` definitions. Undefined `U` imports cannot satisfy monolithic code presence.
- `review_graph.py`: deterministic read-only command/path/DAG review of exported actions, with the actual provider definition and its object-to-link response/dependency join. It writes a new review alongside the graph; it does not execute native actions.

All Python imports are local tracked modules. No runtime import or implicit lookup reaches `output/unreal` code. `cook_binding.py`, the engine patch/verifier and the finalizer are also canonical source; their separate source/build/cook/container checks remain required.

## Explicit inputs

Every source/plan command requires `--engine`, `--project`, `--run-root`. The engine must contain a real `.brezi-isolated-engine` file whose value is that exact canonical absolute root. Project must be a real BreziTwin clone inside that marked engine. Run root must be inside engine `.brezi-managed` and outside the project. The runner does not create or trust a marker implicitly, copy the engine, patch managed assemblies, or touch stock UE.

`--toolchain-pins FILE --toolchain-sha256 SHA` selects a reviewed JSON `{ "fileHashes": { "/absolute/candidate/file": "sha256", … } }`. It must cover bundled dotnet, AutomationTool.dll, both UBT/AT copies of UnrealBuildTool.dll and EpicGames.Build.dll, and candidate `BuildConfiguration.xml`; extra candidate-local dependency pins are retained. This makes the managed UBT/AT bootstrap an explicit prerequisite instead of silently using the old candidate's hardcoded assembly hashes. The v1 source patch alone does not prepare those tools.

`source --engine-manifest …` verifies the v1 combined engine patch/result hashes and records current Source/Config/Build/Content/plugin files, project descriptor, engine source and toolchain. Exactly `Build/Mac/BreziTwin.PackageVersionCounter` and the two `Build/Mac/FileOpenOrder/{EditorOpenOrder,CookerOpenOrder}.log` files are recorded as generated metadata instead of immutable authoring input. Source additions/deletions and all other source byte changes fail every phase.

## Future commands (not executed here)

After adopting the staged files and explicitly preparing the isolated engine/project/toolchain:

```sh
python3 -B scripts/unreal/caustics/phase_runner.py source \
  --engine "$BREZI_ENGINE" --project "$BREZI_PROJECT" --run-root "$BREZI_RUNS" \
  --toolchain-pins "$BREZI_TOOLS_RECEIPT" --toolchain-sha256 "$BREZI_TOOLS_SHA" \
  --engine-manifest scripts/unreal/engine-overlays/ue-5.8.2-floor-caustics/manifest.json \
  --output "$BREZI_RUNS/source.json"

python3 -B scripts/unreal/caustics/phase_runner.py plan editor-graph --attempt first \
  --engine "$BREZI_ENGINE" --project "$BREZI_PROJECT" --run-root "$BREZI_RUNS" \
  --toolchain-pins "$BREZI_TOOLS_RECEIPT" --toolchain-sha256 "$BREZI_TOOLS_SHA" \
  --source-closure "$BREZI_RUNS/source.json" --output "$BREZI_RUNS/editor-graph-plan.json"

python3 -B scripts/unreal/caustics/phase_runner.py run \
  --plan "$BREZI_RUNS/editor-graph-plan.json" --sha256 "$BREZI_PLAN_SHA" --check
```

Run omitting `--check` only when that exact planned native phase is authorized. Plan receipt supplies the native attempt directory and, for cook, the fresh cook-output path before it exists. Run reconstructs exact argv/configuration and refuses edited plans or helpers. A run never automatically retries.

Graph phases export metadata only. Independent graph review must be saved alongside `actions.json` as a JSON with `status:"pass"`, `issues:[]`, `graphSha256` and nonempty `providerCompileActions` whose `apiEnabled` values are true. Build plans require `--graph-review` and check the matching successful graph process, source closure, target, engine and project. This runner does not invent graph approval. After a clean Editor/Game build, invoke `accept_build.py editor|game` with the same paths plus `--source-closure`, `--graph-review`, `--build-receipt`, and a new `--output`.

After the exact graph phase closes, review its exported file:

```sh
python3 -B scripts/unreal/caustics/review_graph.py \
  --engine "$BREZI_ENGINE" --project "$BREZI_PROJECT" \
  --graph "$BREZI_GRAPH_DIRECTORY/actions.json"
```

The default new output is `graph-review.json` beside `actions.json`; pass that to the matching build plan. Existing files are never overwritten. Review checks current forced definitions, source/response files, captured-versus-current RSP tokens, closed action command types, declared outputs/deletions inside the selected project or shared Engine, and prerequisite cycles/missing IDs. Every scheduled provider object must reach the actual Game or provider-dylib link through both its response and prerequisite edges. `sharedEngineProducedPaths` identifies engine products the graph proposes to rewrite; inspect those before reusing an engine with frozen historical receipts. Exported actions do not enumerate every Xcode/cache side effect, and this review is not a sandbox or proof of completed native compilation/linkage.

The schema comes from UE5.8 UBT `Actions/Action.cs:675–716` (`ExportJson`, including embedded response contents and prerequisite IDs); `Actions/ActionGraph.cs:1017–1048` assigns those IDs within the exported subset. Completed native symbol/module evidence remains the separate `accept_build.py` step.

An empty/cache-only provider compile set fails the current build-acceptance interface explicitly; no cached object is labeled a fresh compile. A future reuse path needs actual prior-object provenance and acceptance support. Stored Editor02 (46 actions, one provider compile) passes; stored Game03 (71 actions, three provider compiles) retains valid provider/link edges but now rejects two subsequently regenerated PCH RSPs. These read-only regression checks preserve that historical drift without rewriting its old receipts. Run the bounded tests with `python3 -B scripts/unreal/caustics/test_review_graph.py` and `python3 -B -O scripts/unreal/caustics/test_review_graph.py`.

For `cook`/`archive` plans, pass both `--accepted-editor` and `--accepted-game`. Cook retains candidate `.ddc`, NullRHI, current map, one cook process and the existing four-worker settings. DDC must already exist; there is no implicit copy or remote cache setup. Before executing cook, call the v1 tracked `cook_binding.py before` with the planned cook output and the explicitly located pinned historical Editor pair.

Archive additionally requires `--cook-receipt`. It uses the actual accepted fresh cook, `-skipbuild -skipcook`, explicit staging/archive paths, and one argv element:

```
-xcodebuildoptions=-derivedDataPath "<new attempt>/xcode-derived-data"
```

UE5.8 `ProjectParams.cs:1133` parses that field; `ApplePlatform.Automation.cs:143–146,272–275` forwards it to both Stage and Package. UBT's ordinary postbuild does not expose the same option, so it is restricted to UAT. Build/cook/archive use the ordinary authorized local CLI/Xcode environment, with no custom Seatbelt wrapper or provisioning-update option. Source and native inputs remain pinned; this is not a claim all ordinary Xcode/cache writes are sandbox-confined.

## Actual failure semantics retained

- UAT `ExitCode=0` / `BUILD SUCCESSFUL` never overrides `** BUILD FAILED **` or `The following build commands failed:` anywhere in captured logs. The native exit remains recorded as zero but phase validation fails.
- A legitimate Editor shader cache miss before successful compilation is not treated as a material fallback. Compile errors, invalid shader maps, ensures and explicit material compilation failure still reject.
- Clean builds record actual `buildOutputHashes` after native exit; acceptance rechecks them before and after its symbol/module/snapshot work.
- Game postbuild `P/Binaries/Mac/BreziTwin.app` is mutable packaging output. Acceptance copies it to a new independent historical snapshot, verifies both trees and distinct inodes, and pins only that copy. Current inputs retain raw `BreziTwin`, `.target`, source, Editor DLLs and module mappings. Receipts that still pin the original mutable app are rejected, not silently filtered.
- A failed build is never relabeled successful. The one-off delivery's separately ordered Xcode/version/metadata recovery stays preserved as historical evidence; this clean reusable runner requires a clean build. If an ordinary future build needs a recovery path, inspect its actual failure first.
- Graph/build/cook/archive status is distinct from package sealing, actual standalone launch, continuous motion, visual quality and performance. The existing strict detached binding / IoStore listing / finalizer join remains mandatory after archive.

## Remaining integration ownership

The modules are canonical. The remaining integration is to wire the existing `scripts/unreal/run.mjs` continuous branch to explicit source→graph review→build acceptance→fresh cook→archive→actual IoStore listing→detached binding→sealing. Keep its current canonical import gates and deliberate final package-report schema join. Candidate managed-engine/bootstrap reproducibility and historical proof relocation remain explicit external prerequisites; no code here fabricates either.
