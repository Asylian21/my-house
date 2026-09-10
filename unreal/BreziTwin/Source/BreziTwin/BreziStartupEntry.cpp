// App-owned LC_MAIN entry; the installed engine and its main implementation are untouched.
// Self-exec refreshes OS process arguments before NSProcessInfo caches them. No helper
// executable, private API, CRT mutation, Cocoa call or UE allocation is used here.
#if defined(__APPLE__) && (defined(BREZI_STARTUP_ENTRY_FIXTURE) || (defined(UE_GAME) && UE_GAME))
#include <errno.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>
#include <unistd.h>

extern "C" int BreziEngineMain(int argc, char** argv) __asm("_main");
namespace {
constexpr int MaxArguments = 4096;
int Fail(const char* message)
{
    fprintf(stderr, "BreziStartupEntry: rejected=%s\n", message);
    return 64;
}
bool Exact(const char* argument, const char* flag)
{
    return argument && (argument[0] == '-' || argument[0] == '/') && strcasecmp(argument + 1, flag) == 0;
}
bool Valued(const char* argument, const char* flag)
{
    if (!argument || (argument[0] != '-' && argument[0] != '/')) return false;
    const size_t length = strlen(flag);
    return strncasecmp(argument + 1, flag, length) == 0 &&
        (argument[length + 1] == '=' || argument[length + 1] == ':');
}
}
extern "C" __attribute__((visibility("default"), used)) int BreziMain(int argc, char** argv)
{
    if (!argv || argc < 1 || argc > MaxArguments || argv[argc] != nullptr) return Fail("argument-count");
    bool canonicalLlm = false, canonicalHitches = false;
    for (int index = 1; index < argc; ++index)
    {
        if (!argv[index]) return Fail("null-argument");
        if (Exact(argv[index], "NOLLM") || Valued(argv[index], "NOLLM") ||
            Valued(argv[index], "LLM") || Valued(argv[index], "DetectHitchesWithLLM")) return Fail("conflicting-policy");
        canonicalLlm |= strcmp(argv[index], "-LLM") == 0;
        canonicalHitches |= strcmp(argv[index], "-DetectHitchesWithLLM") == 0;
    }
    if (canonicalLlm && canonicalHitches)
    {
        fprintf(stderr, "BreziStartupEntry: pid=%d phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM\n", (int)getpid());
        return BreziEngineMain(argc, argv);
    }
    // We add these exact tokens, so the next entry takes the branch above. No
    // environment sentinel, timer, retry, or potentially stale argv cache is used.
    if (argc > MaxArguments - 2) return Fail("argument-capacity");
    char path[PATH_MAX], executable[PATH_MAX];
    uint32_t capacity = sizeof(path);
    if (_NSGetExecutablePath(path, &capacity) != 0 || !realpath(path, executable)) return Fail("executable-path");
    const char* suffix = "/Contents/MacOS/BreziTwin";
    const size_t length = strlen(executable), suffixLength = strlen(suffix);
    if (length <= suffixLength || strcmp(executable + length - suffixLength, suffix) != 0) return Fail("expected-original-bundle-main");
    struct stat info;
    if (lstat(executable, &info) || !S_ISREG(info.st_mode) || access(executable, X_OK)) return Fail("executable-file");
    char** forwarded = (char**)calloc((size_t)argc + 3, sizeof(char*));
    if (!forwarded) return Fail("argument-allocation");
    forwarded[0] = executable;
    forwarded[1] = (char*)"-LLM";
    forwarded[2] = (char*)"-DetectHitchesWithLLM";
    for (int index = 1; index < argc; ++index) forwarded[index + 2] = argv[index];
    fprintf(stderr, "BreziStartupEntry: pid=%d phase=self-exec forcedFlags=-LLM,-DetectHitchesWithLLM\n", (int)getpid());
    execv(executable, forwarded);
    const int failure = errno;
    free(forwarded);
    fprintf(stderr, "BreziStartupEntry: execv-failed-errno=%d\n", failure);
    return 126;
}
#endif
