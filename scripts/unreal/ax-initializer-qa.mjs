/** Inspect native lifecycle observations, never infer VoiceOver speech coverage. */
export function inspectAXInitializer(receipt, stressRequested = false) {
  const errors = [];
  const check = (condition, message) => { if (!condition) errors.push(message); };
  check(receipt?.installedAtObjectiveCLoad === true && receipt?.installationError === "none"
    && receipt?.engineGuard === "5.8.2-56702186-non-licensee", "Native AX initializer repair was not installed for the reviewed engine");
  check(receipt?.engineDeallocUnchanged === true, "Engine AX dealloc policy differs");
  check(receipt?.phase === "queues-drained-before-slate-shutdown" && receipt?.shutdownStarted === true
    && receipt?.outstanding === 0, "Native AX initialization did not finish a drained shutdown");
  check(Number.isSafeInteger(receipt?.applied) && receipt.applied > 0, "No real native AX initialization was applied");
  check(receipt?.stressRequested === stressRequested, "Native AX stress mode differs from this invocation");
  if (stressRequested) {
    check(receipt?.stressFinished === true && receipt?.stressPassed === true
      && receipt?.stressAbsentIdCount === 16 && receipt?.stressMissingWidgetDrops === 32
      && receipt?.stressStaleGenerationDrops === 16, "Native absent-ID and stale-generation stress did not pass");
  }
  return { status: errors.length ? "failed" : "native-ax-initializer-lifecycle-observed", stressRequested, errors,
    scope: "Installed initializer, actual applied native values, optional absent-ID/generation rejection and drained process shutdown. This does not certify VoiceOver speech, all focus paths or general engine accessibility behavior." };
}
