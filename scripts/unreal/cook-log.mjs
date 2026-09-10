/** UAT can exit zero after replacing a failed project shader with Default Material. */
export function inspectCookLog(log) {
  const failures = log.split(/\r?\n/).flatMap((line, index) =>
    /Failed to compile Material|Default Material will be used in game|LogShaderCompilers:\s*Error:|Tried to access an uncooked shader map/i.test(line)
      ? [{ line: index + 1, message: line.trim() }] : []);
  const cookCompleted = log.includes("COOK COMMAND COMPLETED");
  return { status: !cookCompleted ? "cook-completion-unconfirmed" : failures.length ? "material-compilation-failed" : "cook-log-validated",
    cookCompleted, failures,
    verification: "Cook completion and absence of reported shader fallback; rendered appearance requires runtime QA" };
}
