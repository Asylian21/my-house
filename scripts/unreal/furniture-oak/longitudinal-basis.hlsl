// Exact axial tabletop/chair rail boxes only. Unreal centimetres.
// Image V follows the long site-X axis on broad faces. End-face veneer is
// an explicit transverse appearance approximation, not measured end grain.
float3 N = normalize(NormalWS);
float3 A = abs(N);
float3 T, V;
if (A.x >= A.y && A.x >= A.z) {
    T = float3(0, -sign(N.x), 0);
    V = float3(0, 0, -1);
} else if (A.y >= A.z) {
    T = float3(0, 0, sign(N.y));
    V = float3(1, 0, 0);
} else {
    T = float3(0, -sign(N.z), 0);
    V = float3(1, 0, 0);
}
