// Authored, bounded visual flame. Relative emissive units, not radiometry.
// No WPO: every animated pixel remains inside the verified card/chamber bounds.
float phase = floor(UV.x * 0.5);
float2 p = float2(UV.x - phase * 2.0, UV.y);
float t = Time * 1.35 + phase * 1.71;
float rise = p.y * 6.2 - t * 2.1;
float sway = (0.065 * sin(rise + phase) + 0.028 * sin(rise * 2.7 - t)) * p.y;
float center = 0.5 + sway;
float width = 0.33 * pow(saturate(1.0-p.y), 0.65);
width *= 0.83 + 0.17 * sin(rise * 2.3 + sin(t + p.y * 11.0));
float side = abs(p.x-center);
// Alpha-only proposal: a connected low body and two unequal, changing lobes.
// Both crossed cards retain the existing phase; no extra geometry or texture.
float aa = max(fwidth(UV.x), 0.006);
float bodyCenter = 0.5 + 0.018 * sin(Time * 0.73 + p.y * 6.0);
float bodyWidth = 0.45 - 0.06 * p.y;
float body = (1.0-smoothstep(bodyWidth-aa,bodyWidth+aa,abs(p.x-bodyCenter)))
           * (1.0-smoothstep(0.14,0.40,p.y));

float heightA = 0.58 + 0.33 * (0.5 + 0.5*sin(Time*1.13 + phase*2.31));
float heightB = 0.40 + 0.40 * (0.5 + 0.5*sin(Time*1.59 + phase*1.17 + 2.2));
float remainingA = saturate(1.0-p.y/heightA);
float remainingB = saturate(1.0-p.y/heightB);
float centerA = 0.39 + p.y*(0.085*sin(rise*0.91 + phase) + 0.07);
float centerB = 0.66 + p.y*(0.070*sin(rise*1.37 - phase) - 0.13);
float widthA = 0.235 * remainingA * (1.25-0.25*remainingA);
float widthB = 0.180 * remainingB * (1.25-0.25*remainingB);
float lobeA = (1.0-smoothstep(widthA-aa,widthA+aa,abs(p.x-centerA)))
            * (1.0-smoothstep(heightA-0.05,heightA,p.y));
float lobeB = (1.0-smoothstep(widthB-aa,widthB+aa,abs(p.x-centerB)))
            * (1.0-smoothstep(heightB-0.05,heightB,p.y));

// Two upward-moving bands pinch/split only the upper flame. No frac(time) jumps.
float breakup = 0.5 + 0.25*sin(p.x*19.0 + rise*1.3)
                    + 0.25*sin(p.x*37.0 - rise*2.6 + sin(Time*0.7 + phase));
float continuity = lerp(1.0, smoothstep(0.20,0.50,breakup), smoothstep(0.20,0.65,p.y));
float edge = smoothstep(0.0,0.035,p.x) * (1.0-smoothstep(0.965,1.0,p.x))
           * smoothstep(0.0,0.045,p.y) * (1.0-smoothstep(0.91,0.99,p.y));
float shape = max(body,max(lobeA,lobeB)) * continuity * edge;
float curl = 0.74 + 0.26 * sin(rise * 2.9 + p.x * 16.0 + sin(t * 1.3));
float core = saturate(1.0-side/max(width*0.58,0.001)) * saturate(1.0-p.y*1.7);
float3 color = lerp(float3(1.0,0.12,0.006),float3(1.0,0.68,0.19),core);
return float4(color * (3.0 + 5.0 * core) * curl, saturate(shape * (0.58+0.20*core)));
