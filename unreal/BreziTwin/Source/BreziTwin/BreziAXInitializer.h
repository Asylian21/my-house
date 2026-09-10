#pragma once

namespace BreziAXInitializer
{
    // The Objective-C +load hook installs before standalone app main, including
    // when system VoiceOver is already enabled. This validates the early result.
    bool VerifyInstalled();
    void RunStressIfRequested();
    void BeginShutdown();
    void WriteReceipt(const char* Phase);
}
