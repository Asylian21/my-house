// Procedural char and ash over source-bound derived logs. Not a wood scan.
float stripe = abs(sin((UV.x * 29.0 + 0.17*sin(UV.y*18.0)) * 3.14159265));
float crossGrain = abs(sin((UV.y * 19.0 + 0.12*sin(UV.x*43.0)) * 3.14159265));
float aa = max(fwidth(stripe),0.01);
float crack = (1.0-smoothstep(0.025-aa,0.07+aa,stripe));
crack *= 0.28 + 0.72*(1.0-smoothstep(0.08,0.38,crossGrain));
return saturate(crack);
