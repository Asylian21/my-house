/* App-scoped entry point, installed only by the reviewed packaging step.
 * Finder -> this signed Mach-O -> execv the re-signed UE sibling, same PID.
 * Engine code/data are unchanged; signing metadata uses inherited sandboxing.
 * No Cocoa, UE allocator, shell, child process, or writable command-line file.
 */
#include <errno.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>
#include <unistd.h>

enum { MaxArguments = 4096 };

static int Fail(const char *message)
{
    fprintf(stderr, "BreziStartupLauncher: %s\n", message);
    return 64;
}

static int IsExactFlag(const char *argument, const char *flag)
{
    return argument && (argument[0] == '-' || argument[0] == '/') &&
        strcasecmp(argument + 1, flag) == 0;
}

static int IsFlagWithValue(const char *argument, const char *flag)
{
    if (!argument || (argument[0] != '-' && argument[0] != '/')) return 0;
    const size_t size = strlen(flag);
    return strncasecmp(argument + 1, flag, size) == 0 &&
        (argument[size + 1] == '=' || argument[size + 1] == ':');
}

int main(int argc, char **argv)
{
    if (argc < 1 || argc > MaxArguments) return Fail("Invalid argument count");
    for (int index = 1; index < argc; ++index)
    {
        /* Reject contradictory/ambiguous requests instead of silently overriding
         * them. All accepted original argument strings remain byte-for-byte.
         * Exact duplicate -LLM is harmless to UE FParse::Param.
         */
        if (IsExactFlag(argv[index], "NOLLM") || IsFlagWithValue(argv[index], "NOLLM") ||
            IsFlagWithValue(argv[index], "LLM") || IsFlagWithValue(argv[index], "DetectHitchesWithLLM"))
            return Fail("This bundle requires LLM and DetectHitchesWithLLM; contradictory or valued forms are unsupported");
    }

    char self[PATH_MAX], canonicalSelf[PATH_MAX], directory[PATH_MAX], target[PATH_MAX];
    uint32_t capacity = sizeof(self);
    if (_NSGetExecutablePath(self, &capacity) != 0 || !realpath(self, canonicalSelf))
        return Fail("Cannot resolve this executable");
    if (strlen(canonicalSelf) >= sizeof(directory)) return Fail("Executable path too long");
    strcpy(directory, canonicalSelf);
    char *slash = strrchr(directory, '/');
    if (!slash || strcmp(slash + 1, "BreziStartupLauncher") != 0)
        return Fail("Expected bundled executable BreziStartupLauncher");
    *slash = '\0';
    const char *suffix = "/Contents/MacOS";
    const size_t dirSize = strlen(directory), suffixSize = strlen(suffix);
    if (dirSize <= suffixSize || strcmp(directory + dirSize - suffixSize, suffix) != 0)
        return Fail("Launcher is not in Contents/MacOS");
    if (snprintf(target, sizeof(target), "%s/BreziTwin", directory) >= (int)sizeof(target))
        return Fail("Game executable path too long");
    struct stat info;
    if (lstat(target, &info) != 0 || !S_ISREG(info.st_mode) || S_ISLNK(info.st_mode) ||
        access(target, X_OK) != 0)
        return Fail("Missing regular executable sibling BreziTwin");

    char **forwarded = calloc((size_t)argc + 3, sizeof(char *));
    if (!forwarded) return Fail("Cannot allocate bounded argument vector");
    forwarded[0] = target;
    forwarded[1] = "-LLM";
    forwarded[2] = "-DetectHitchesWithLLM";
    for (int index = 1; index < argc; ++index) forwarded[index + 2] = argv[index];
    /* Deliberately do not log user arguments. The parent QA process records its
     * own known arguments and observes the same PID before/after exec.
     */
    fprintf(stderr, "BreziStartupLauncher: pid=%d exec-sibling=BreziTwin forcedFlags=-LLM,-DetectHitchesWithLLM\n", (int)getpid());
    execv(target, forwarded);
    const int failure = errno;
    free(forwarded);
    fprintf(stderr, "BreziStartupLauncher: execv failed errno=%d\n", failure);
    return 126;
}
