// Dom's app-owned LC_MAIN entry. The accepted scene and installed engine are unchanged.
// Finder receives the accepted exterior viewer defaults; explicit CLI/QA arguments
// retain their full semantics, including capture size and camera ownership.
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
constexpr const char* DomDefaults[] = {"-windowed", "-ResX=1920", "-ResY=1080", "-BreziOutput=retina",
    "-BreziRenderProfile=full", "-BreziView=exterior-neighborhood-ground-r38"};
constexpr int DomDefaultCount = sizeof(DomDefaults) / sizeof(DomDefaults[0]);
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
    bool canonicalLlm = false, canonicalHitches = false, explicitArguments = false;
    for (int index = 1; index < argc; ++index)
    {
        if (!argv[index]) return Fail("null-argument");
        if (Exact(argv[index], "NOLLM") || Valued(argv[index], "NOLLM") ||
            Valued(argv[index], "LLM") || Valued(argv[index], "DetectHitchesWithLLM")) return Fail("conflicting-policy");
        canonicalLlm |= strcmp(argv[index], "-LLM") == 0;
        canonicalHitches |= strcmp(argv[index], "-DetectHitchesWithLLM") == 0;
        if (!Exact(argv[index], "LLM") && !Exact(argv[index], "DetectHitchesWithLLM")
            && strncmp(argv[index], "-psn_", 5) != 0) explicitArguments = true;
    }
    const bool addDomDefaults = !explicitArguments;
    const bool addStartupFlags = !(canonicalLlm && canonicalHitches);
    if (!addStartupFlags && !addDomDefaults)
    {
        fprintf(stderr, "BreziStartupEntry: pid=%d phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM\n", (int)getpid());
        return BreziEngineMain(argc, argv);
    }
    // Defaults are ordinary OS argv tokens on the next entry. They make that
    // entry explicit, so it takes the engine branch without a restart sentinel.
    const int additions = (addStartupFlags ? 2 : 0) + (addDomDefaults ? DomDefaultCount : 0);
    if (argc > MaxArguments - additions) return Fail("argument-capacity");
    char path[PATH_MAX], executable[PATH_MAX];
    uint32_t capacity = sizeof(path);
    if (_NSGetExecutablePath(path, &capacity) != 0 || !realpath(path, executable)) return Fail("executable-path");
    const char* suffix = "/Contents/MacOS/BreziTwin";
    const size_t length = strlen(executable), suffixLength = strlen(suffix);
    if (length <= suffixLength || strcmp(executable + length - suffixLength, suffix) != 0) return Fail("expected-original-bundle-main");
    struct stat info;
    if (lstat(executable, &info) || !S_ISREG(info.st_mode) || access(executable, X_OK)) return Fail("executable-file");
    char** forwarded = (char**)calloc((size_t)argc + additions + 1, sizeof(char*));
    if (!forwarded) return Fail("argument-allocation");
    int destination = 0;
    forwarded[destination++] = executable;
    if (addStartupFlags)
    {
        forwarded[destination++] = (char*)"-LLM";
        forwarded[destination++] = (char*)"-DetectHitchesWithLLM";
    }
    if (addDomDefaults)
    {
        for (const char* argument : DomDefaults) forwarded[destination++] = (char*)argument;
        fprintf(stderr, "DomStartupDefaults: pid=%d camera=exterior-neighborhood-ground-r38 profile=full output=retina\n", (int)getpid());
    }
    for (int index = 1; index < argc; ++index) forwarded[destination++] = argv[index];
    fprintf(stderr, "BreziStartupEntry: pid=%d phase=self-exec forcedFlags=-LLM,-DetectHitchesWithLLM\n", (int)getpid());
    execv(executable, forwarded);
    const int failure = errno;
    free(forwarded);
    fprintf(stderr, "BreziStartupEntry: execv-failed-errno=%d\n", failure);
    return 126;
}
#endif
