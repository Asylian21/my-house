#pragma once
// Detached post-archive proof: generated only from a clean cook/package and
// accepted Editor geometry/wave evidence. The final sealed payload receipt
// binds this JSON externally; it is not a signature or a new trust protocol.
#include "CoreMinimal.h"
#include "BreziCausticsWaterBinding.h"
#include "BreziSceneRevision.h"
#include "HAL/PlatformFile.h"
#include "HAL/PlatformProperties.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"

namespace BreziCookedSceneBinding
{
static constexpr const TCHAR* ExpectedBinding = BreziSceneRevision::BindingSha256;
static constexpr const TCHAR* ExpectedWater = BreziSceneRevision::WaterSha256;
static constexpr const TCHAR* ExpectedMap = BreziSceneRevision::MapSha256;
class FVerifiedPackage;
inline bool VerifyPackage(const FString&,const FString&,FVerifiedPackage&,FString&);
class FVerifiedPackage
{
    friend bool VerifyPackage(const FString&,const FString&,FVerifiedPackage&,FString&);
    bool bVerified=false;
    FString ReceiptHash;
    TMap<FString,FString> SourceAssets;
public:
    bool IsVerified() const { return bVerified; }
    const FString& ReceiptSha1() const { return ReceiptHash; }
    bool CoversSourceAsset(const FString& Path,const FString& Sha1) const
    { const FString* Expected=SourceAssets.Find(Path);return bVerified && Expected && Expected->Equals(Sha1,ESearchCase::IgnoreCase); }
};
inline bool Fail(FString& Error,const FString& Why){Error=Why;return false;}
inline bool Hex(const FString& V,int32 Count)
{
    if(V.Len()!=Count)return false;
    for(TCHAR C:V)if(!((C>='0'&&C<='9')||(C>='a'&&C<='f')))return false;
    return true;
}
inline bool HashPhysical(const FString& Path,int64 ExpectedSize,const FString& ExpectedHash)
{
    TUniquePtr<IFileHandle> File(IPlatformFile::GetPlatformPhysical().OpenRead(*Path));
    if(!File || ExpectedSize<=0 || File->Size()!=ExpectedSize || !Hex(ExpectedHash,40))return false;
    FSHA1 Hash;TArray<uint8> Buffer;Buffer.SetNumUninitialized(1024*1024);int64 Left=ExpectedSize;
    while(Left>0){const int32 Count=int32(FMath::Min<int64>(Left,Buffer.Num()));if(!File->Read(Buffer.GetData(),Count))return false;Hash.Update(Buffer.GetData(),Count);Left-=Count;}
    Hash.Final();uint8 Bytes[FSHA1::DigestSize];Hash.GetHash(Bytes);
    return File->Size()==ExpectedSize && BytesToHex(Bytes,FSHA1::DigestSize).Equals(ExpectedHash,ESearchCase::IgnoreCase);
}
// Worker-safe: every input is an immutable path or worker-local value. No UObject access.
// GT must adopt the completed token; do not inspect the token while this call writes it.
inline bool VerifyPackage(const FString& ReceiptPath,const FString& AbsolutePakDirectory,FVerifiedPackage& Out,FString& Error)
{
    if(Out.IsVerified() || FPaths::IsRelative(ReceiptPath) || FPaths::IsRelative(AbsolutePakDirectory))
        return Fail(Error,TEXT("Cooked package verification requires new token and absolute paths"));
    Out=FVerifiedPackage();TArray<uint8> Bytes;
    if(!FFileHelper::LoadFileToArray(Bytes,*ReceiptPath))return Fail(Error,TEXT("Missing post-archive cooked binding receipt"));
    FString Text;FFileHelper::BufferToString(Text,Bytes.GetData(),Bytes.Num());TSharedPtr<FJsonObject> J;
    if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J) || !J.IsValid())return Fail(Error,TEXT("Malformed cooked binding receipt"));
    if(J->GetIntegerField(TEXT("schemaVersion"))!=1 || J->GetStringField(TEXT("status"))!=TEXT("cooked-source-container-lineage-validated")
       || J->GetStringField(TEXT("sourceBindingSha256"))!=ExpectedBinding
       || J->GetStringField(TEXT("activeWaterBindingSha256"))!=ExpectedWater || J->GetStringField(TEXT("sourceMapSha256"))!=ExpectedMap
       || J->GetIntegerField(TEXT("receiverCount"))!=45 || J->GetIntegerField(TEXT("waterCount"))!=1
       || J->GetIntegerField(TEXT("receiverTriangles"))!=1076 || J->GetIntegerField(TEXT("waterTriangles"))!=4608
       || J->GetIntegerField(TEXT("waveCount"))!=12 || !J->GetBoolField(TEXT("sourcePinsUnchangedAcrossCookAndArchive"))
       || !J->GetBoolField(TEXT("freshCookOutput")) || !J->GetBoolField(TEXT("allRequiredPackagesInContainer"))
       || J->GetBoolField(TEXT("runtimeTriangleBijectionReexecuted")) || J->GetBoolField(TEXT("fullOpticsValidated")))
        return Fail(Error,TEXT("Cooked binding source/proof policy differs"));
    // The pair is produced after the immutable Editor build. Its exact bytes
    // and both native captures are checked by cook/seal and the sealed payload.
    // Compiling that future hash would invalidate the source used by the pair.
    const FString Pair=J->GetStringField(TEXT("editorPairSha256"));
    if(FCString::Strlen(BreziSceneRevision::AuthoritySha256)>0)
    {
        FString Authority;
        if(!J->TryGetStringField(TEXT("sourceAuthoritySha256"),Authority)
           || Authority!=BreziSceneRevision::AuthoritySha256 || !Hex(Pair,64))
            return Fail(Error,TEXT("Cooked binding source revision/pair identity differs"));
    }
    else if(Pair!=BreziSceneRevision::LegacyEditorPairSha256)
        return Fail(Error,TEXT("Legacy cooked pair identity differs"));
    for(const TCHAR* Key:{TEXT("sourceSnapshotSha256"),TEXT("cookReceiptSha256"),TEXT("archiveReceiptSha256"),TEXT("ioStoreListingSha256")})
        if(!Hex(J->GetStringField(Key),64))return Fail(Error,TEXT("Missing actual delivery evidence identity"));
    const auto Source=J->GetObjectField(TEXT("sourceAssetHashes"));
    if(Source->Values.Num()!=55)return Fail(Error,TEXT("Cooked binding source asset scope differs"));
    for(const auto& Row:Source->Values)
    {
        const FString Key(*Row.Key),H=Row.Value->AsObject()->GetStringField(TEXT("sha1"));
        if(!Key.StartsWith(TEXT("Content/Brezi/")) || Key.Contains(TEXT("..")) || !Hex(H,40))return Fail(Error,TEXT("Invalid source asset entry"));
        Out.SourceAssets.Add(Key,H);
    }
    if(Out.SourceAssets.FindRef(BreziCausticsWaterMaterialRelativePath)!=BreziCausticsWaterMaterialSha1)
        return Fail(Error,TEXT("Cooked lineage names another saved water graph"));
    const FString PakDir=AbsolutePakDirectory;
    TSet<FString> ExpectedNames;
    for(const auto& Value:J->GetArrayField(TEXT("containerFiles")))
    {
        const auto Row=Value->AsObject();const FString Name=Row->GetStringField(TEXT("name"));
        if(Name.IsEmpty() || FPaths::GetCleanFilename(Name)!=Name || Name.Contains(TEXT("..")) || ExpectedNames.Contains(Name)
           || !Hex(Row->GetStringField(TEXT("sha256")),64)
           || !HashPhysical(PakDir/Name,int64(Row->GetNumberField(TEXT("bytes"))),Row->GetStringField(TEXT("sha1"))))
            return Fail(Error,TEXT("Cooked container bytes differ or invalid entry"));
        ExpectedNames.Add(Name);
    }
    for(const TCHAR* Name:{TEXT("BreziTwin-Mac.pak"),TEXT("BreziTwin-Mac.utoc"),TEXT("BreziTwin-Mac.ucas"),TEXT("global.utoc"),TEXT("global.ucas")})
        if(!ExpectedNames.Contains(Name))return Fail(Error,TEXT("Incomplete standalone container set"));
    TSet<FString> ActualNames;bool bUnexpectedDirectory=false;
    if(!IPlatformFile::GetPlatformPhysical().IterateDirectory(*PakDir,[&](const TCHAR* Path,bool bDirectory)
       {if(bDirectory)bUnexpectedDirectory=true;else ActualNames.Add(FPaths::GetCleanFilename(Path));return true;})
       || bUnexpectedDirectory || ActualNames.Num()!=ExpectedNames.Num())return Fail(Error,TEXT("Container directory scope differs"));
    for(const FString& Name:ActualNames)if(!ExpectedNames.Contains(Name))return Fail(Error,TEXT("Undeclared container/patch file"));
    uint8 Hash[FSHA1::DigestSize];FSHA1::HashBuffer(Bytes.GetData(),Bytes.Num(),Hash);
    Out.ReceiptHash=BytesToHex(Hash,FSHA1::DigestSize).ToLower();Out.bVerified=true;return true;
}
inline bool VerifyPackage_GT(const FString& ReceiptPath,FVerifiedPackage& Out,FString& Error)
{
    if(!IsInGameThread() || !FPlatformProperties::RequiresCookedData())return Fail(Error,TEXT("Expected cooked GameThread initialization"));
    return VerifyPackage(FPaths::ConvertRelativePathToFull(ReceiptPath),FPaths::ConvertRelativePathToFull(FPaths::ProjectContentDir()/TEXT("Paks")),Out,Error);
}

}
