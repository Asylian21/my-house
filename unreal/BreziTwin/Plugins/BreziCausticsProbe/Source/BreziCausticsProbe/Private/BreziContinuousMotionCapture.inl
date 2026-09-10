// Included inside the provider's private namespace, after its JSON/readback helpers.
// Optional 64-frame evidence only; ordinary continuous use never constructs this object.
class FBreziContinuousMotionCapture
{
    struct FFrame
    {
        TSharedPtr<FJsonObject> Meta;
        TUniquePtr<FRHIGPUBufferReadback> Uniform, Gates, Counters;
        TUniquePtr<FRHIGPUTextureReadback> Atlas;
        bool bSaved=false, bCompositeObserved=false;
    };
    const FString Directory;
    TSharedRef<FJsonObject> Meta;
    TArray<FFrame> Frames;
    FString Error;
    bool bWritten=false;
    void Fail(const TCHAR* Why) { if(Error.IsEmpty()) Error=Why; }
    TArray<uint8> Read(FRHIGPUBufferReadback& R,uint32 Count)
    {
        TArray<uint8> Bytes;Bytes.SetNumUninitialized(Count);void* P=R.Lock(Count);
        Require(P!=nullptr,TEXT("Missing continuous motion evidence readback"));
        FMemory::Memcpy(Bytes.GetData(),P,Count);R.Unlock();return Bytes;
    }
    void Save(const FString& Name,const TArray<uint8>& Bytes,const TSharedRef<FJsonObject>& Row)
    {
        Require(FFileHelper::SaveArrayToFile(Bytes,*FPaths::Combine(Directory,Name)),TEXT("Cannot save continuous motion evidence"));
        auto Record=MakeShared<FJsonObject>();Record->SetNumberField(TEXT("bytes"),Bytes.Num());Record->SetStringField(TEXT("sha1"),Sha1(Bytes));
        Row->SetObjectField(Name,Record);
    }
    bool Complete() const
    {
        if(Frames.Num()!=64 || !Error.IsEmpty())return false;
        for(const auto& F:Frames)if(!F.bSaved || !F.bCompositeObserved)return false;
        return true;
    }
    void Write()
    {
        TArray<TSharedPtr<FJsonValue>> Rows;for(const auto& F:Frames)Rows.Add(MakeShared<FJsonValueObject>(F.Meta));
        Meta->SetNumberField(TEXT("motionSchemaVersion"),1);
        Meta->SetStringField(TEXT("status"),Complete()?TEXT("continuous-motion-gpu-readbacks-captured-awaiting-validation"):TEXT("continuous-motion-gpu-readbacks-incomplete"));
        Meta->SetStringField(TEXT("error"),Error);Meta->SetArrayField(TEXT("frames"),Rows);
        Meta->SetNumberField(TEXT("requestedFrameCount"),64);Meta->SetNumberField(TEXT("submittedFrameCount"),Frames.Num());
        Meta->SetBoolField(TEXT("completed"),Complete());Meta->SetBoolField(TEXT("performanceValidated"),false);
        Meta->SetStringField(TEXT("evidenceLayout"),TEXT("36 little-endian bytes: float4 actual Trace View(GameTime,PreExposure,0,0); uint gate; uint4 prepare counters"));
        Meta->SetStringField(TEXT("consumerEvidence"),TEXT("same-frame AfterComposite callback only; no independent consumer shader View uniform readback"));
        SaveJson(Directory,TEXT("motion.json"),Meta);bWritten=true;
    }
public:
    FBreziContinuousMotionCapture(FString InDirectory,TSharedRef<FJsonObject> InMeta):Directory(MoveTemp(InDirectory)),Meta(MoveTemp(InMeta)) { Frames.Reserve(64); }
    void Reject_RT(const TCHAR* Why) { check(IsInRenderingThread());Fail(Why); }
    void Enqueue_RT(FRDGBuilder& GraphBuilder,int32 Index,TSharedRef<FJsonObject> Row,
        const FBreziCausticsProducedGraph& Produced,FRDGBufferRef Counters)
    {
        check(IsInRenderingThread());
        if(!Error.IsEmpty() || bWritten)return;
        if(Index!=Frames.Num() || Index<0 || Index>=64 || !Produced.GPUUniform || !Produced.Gates || !Produced.Atlas || !Counters)
        { Fail(TEXT("Missing, duplicate, reordered or unpaired motion frame"));return; }
        if((Index==52 || Index==63) && (Produced.Atlas->Desc.Format!=PF_FloatRGBA || Produced.Atlas->Desc.Extent!=FIntPoint(512,256) || Produced.Atlas->Desc.NumSamples!=1))
        { Fail(TEXT("Motion atlas format differs"));return; }
        FFrame F;F.Meta=Row;F.Meta->SetBoolField(TEXT("bComposited"),false);
        F.Uniform=MakeUnique<FRHIGPUBufferReadback>(TEXT("Brezi.Continuous.MotionUniform"));
        F.Gates=MakeUnique<FRHIGPUBufferReadback>(TEXT("Brezi.Continuous.MotionGates"));
        F.Counters=MakeUnique<FRHIGPUBufferReadback>(TEXT("Brezi.Continuous.MotionCounters"));
        AddEnqueueCopyPass(GraphBuilder,F.Uniform.Get(),Produced.GPUUniform,16);
        AddEnqueueCopyPass(GraphBuilder,F.Gates.Get(),Produced.Gates,4);
        AddEnqueueCopyPass(GraphBuilder,F.Counters.Get(),Counters,16);
        if(Index==52 || Index==63)
        {
            F.Atlas=MakeUnique<FRHIGPUTextureReadback>(TEXT("Brezi.Continuous.MotionAtlas"));
            AddEnqueueCopyPass(GraphBuilder,F.Atlas.Get(),Produced.Atlas);
        }
        Frames.Add(MoveTemp(F));
    }
    void Composite_RT(uint64 FrameCounter,uint32 FrameNumber,bool bComposited)
    {
        check(IsInRenderingThread());
        for(auto& F:Frames)if(uint64(F.Meta->GetNumberField(TEXT("frameCounter")))==FrameCounter && uint32(F.Meta->GetNumberField(TEXT("frameNumber")))==FrameNumber)
        {
            if(F.bCompositeObserved || !bComposited)Fail(TEXT("Missing or duplicate exact-frame composite"));
            F.bCompositeObserved=true;F.Meta->SetBoolField(TEXT("bComposited"),bComposited);return;
        }
    }
    void Poll_RT()
    {
        check(IsInRenderingThread());if(bWritten)return;
        for(int32 I=0;I<Frames.Num();++I)
        {
            auto& F=Frames[I];if(F.bSaved || !F.Uniform->IsReady() || !F.Gates->IsReady() || !F.Counters->IsReady() || (F.Atlas && !F.Atlas->IsReady()))continue;
            auto Bytes=Read(*F.Uniform,16);Bytes.Append(Read(*F.Gates,4));Bytes.Append(Read(*F.Counters,16));
            float Values[4];uint32 Gate,Counts[4];FMemory::Memcpy(Values,Bytes.GetData(),16);FMemory::Memcpy(&Gate,Bytes.GetData()+16,4);FMemory::Memcpy(Counts,Bytes.GetData()+20,16);
            const bool Finite=FMath::IsFinite(Values[0]) && FMath::IsFinite(Values[1]) && Values[1]>0 && Values[2]==0 && Values[3]==0;
            F.Meta->SetBoolField(TEXT("transportUniformFinite"),Finite);F.Meta->SetNumberField(TEXT("transportGateFlags"),Gate);
            if(Finite){F.Meta->SetNumberField(TEXT("gpuMaterialTimeSeconds"),Values[0]);F.Meta->SetNumberField(TEXT("gpuViewPreExposure"),Values[1]);}
            TArray<TSharedPtr<FJsonValue>> C;for(uint32 V:Counts)C.Add(MakeShared<FJsonValueNumber>(V));F.Meta->SetArrayField(TEXT("prepareCounters"),C);
            Save(FString::Printf(TEXT("frame-%03d-evidence-le.bin"),I),Bytes,F.Meta.ToSharedRef());
            if(F.Atlas)
            {
                int32 Pitch=0,Height=0;void* Data=F.Atlas->Lock(Pitch,&Height);
                Require(Data && Pitch>=512 && Height>=256,TEXT("Motion atlas native pitch invalid"));
                TArray<uint8> Atlas;Atlas.SetNumUninitialized(512*256*8);
                for(int32 Y=0;Y<256;++Y)FMemory::Memcpy(Atlas.GetData()+Y*512*8,static_cast<const uint8*>(Data)+Y*Pitch*8,512*8);
                F.Atlas->Unlock();Save(FString::Printf(TEXT("frame-%03d-atlas-rgba16f-le.bin"),I),Atlas,F.Meta.ToSharedRef());
            }
            F.bSaved=true;F.Uniform.Reset();F.Gates.Reset();F.Counters.Reset();F.Atlas.Reset();
        }
        if(Complete())Write();
    }
    void Drain_RT(FRHICommandListImmediate& RHICmdList)
    {
        check(IsInRenderingThread());
        bool Pending=false;for(const auto& F:Frames)Pending|=!F.bSaved;
        if(Pending) { RHICmdList.SubmitAndBlockUntilGPUIdle();Poll_RT(); }
        if(!bWritten) { if(!Complete())Fail(TEXT("Continuous motion sequence incomplete at shutdown"));Write(); }
        for(auto& F:Frames){F.Uniform.Reset();F.Gates.Reset();F.Counters.Reset();F.Atlas.Reset();}
    }
    void AddLifecycle_GT(const TSharedRef<FJsonObject>& J) const
    {
        check(IsInGameThread()); // Called only after unregister+Drain_RT and FlushRenderingCommands.
        J->SetBoolField(TEXT("motionQACompleted"),Complete());J->SetNumberField(TEXT("motionQASubmittedFrames"),Frames.Num());J->SetStringField(TEXT("motionQAError"),Error);
    }
};
