#include "BreziCollisionAudit.h"
#include "Engine/StaticMesh.h"
#if WITH_EDITOR
#include "StaticMeshResources.h"
#endif

TArray<FVector> UBreziCollisionAudit::ReadLod0Triangles(UStaticMesh* Mesh)
{
    TArray<FVector> Result;
#if WITH_EDITOR
    if (!Mesh || (!Mesh->GetPathName().StartsWith(TEXT("/Game/Brezi/HiddenCollision/"))
        && !Mesh->GetPathName().StartsWith(TEXT("/Game/Brezi/VisualDetails/Stove/")))
        || Mesh->IsCompiling() || !Mesh->GetRenderData() || Mesh->GetRenderData()->LODResources.IsEmpty())
        return Result;
    const FStaticMeshLODResources& LOD = Mesh->GetRenderData()->LODResources[0];
    const uint32 Count = LOD.IndexBuffer.GetNumIndices();
    const uint32 Vertices = LOD.VertexBuffers.PositionVertexBuffer.GetNumVertices();
    if (Count == 0 || Count % 3 != 0 || Count > 3000000 || Vertices == 0)
        return Result;
    Result.Reserve(Count);
    for (uint32 Index = 0; Index < Count; ++Index)
    {
        const uint32 Vertex = LOD.IndexBuffer.GetIndex(Index);
        if (Vertex >= Vertices) return {};
        const FVector Position(LOD.VertexBuffers.PositionVertexBuffer.VertexPosition(Vertex));
        if (Position.ContainsNaN()) return {};
        Result.Add(Position);
    }
#endif
    return Result;
}
