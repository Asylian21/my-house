// Flat source cabinet faces only. Coordinates are Unreal centimetres.
// T is image U/right, V is image V/down. T x V = outward N on every face.
float3 N = normalize(NormalWS);
float3 A = abs(N);
float3 T, V;
if (A.x >= A.y && A.x >= A.z) {
    T = float3(0, -sign(N.x), 0);
    V = float3(0, 0, -1);
} else if (A.y >= A.z) {
    T = float3(sign(N.y), 0, 0);
    V = float3(0, 0, -1);
} else {
    T = float3(0, sign(N.z), 0);
    V = float3(-1, 0, 0);
}
