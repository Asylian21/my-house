# R25 original Fern02 source pilot

This is a source study for one existing own-garden root. It does not change or render an Unreal scene. The native base must be an actually saved R22 integration; that dependency was unavailable when this source plan was generated and remains unbound in the immutable plan.

The official [Poly Haven Fern02](https://polyhaven.com/a/fern_02) asset is [CC0](https://polyhaven.com/license). Its credits distinguish modeling by Rico Cilliers and scanning by Rob Tuytel. Those credits do not establish that the complete plant's 3D geometry was scanned. The plant choice is an artistic trial, without a surveyed botanical or local ecological claim.

All eight consumed published resources match the provider's byte counts and MD5 values; SHA256 values are also recorded. The original four local meshes contain 2,384 / 2,248 / 784 / 816 triangles, totaling 6,232. Their POSITION, NORMAL, UV and indices are decoded without applying the provider's four-clump display translations. The original files have no TANGENT attribute or KHR extensions. All decoded triangles have nonzero geometry and UV area and agree with their mean source normals. The source normals' maximum squared-length error is approximately 0.000098; they are preserved as provided.

The single selected clump is `fern_02_b`, with 1,660 vertices and 2,384 original triangles. The proposed root is `garden_ornamental_10` in the original `DOM_01966` mulch bed. Its exact position and yaw −31° survive. Uniform scale 0.8880718316481575 fits its complete radius inside the old 54.488005106287034 cm envelope. Every decoded vertex and the entire containing circle lie inside the unchanged three-triangle bed union; boundary clearance is 14.521994893713185 cm. The original 48 step triangles and their 112 nonzero projected edges are checked separately. Garden, hardscape and architectural geometry are untouched.

The natural fern form is much lower: 35.272830563130455 cm above the unchanged pivot, replacing a 120 cm grass form. Its original basal vertices extend approximately 2.71 cm below that pivot. They are not lifted, stretched or trimmed. The other 11 ornamental roots and all 461 detailed garden roots remain the original source rows.

The provider glTF says MASK / cutoff 0.5 / double-sided, but its base-color resource is an opaque RGB JPEG. The separately downloaded original Alpha PNG is sixteen-bit grayscale. A future graph must sample its normalized R channel explicitly into Opacity Mask, at cutoff 0.5. Diffuse stays sRGB, original OpenGL normal stays linear with Unreal green-channel flip, and ARM stays linear with roughness from G and metallic fixed to zero. Native import, compression, tangent generation, material readback and actual appearance are still unverified.

The two CPU source previews show the original serrated fronds and varying arching directions using original base color and normalized Alpha.R. They use an orthographic CPU rasterizer and do not evaluate Unreal lighting, normal maps, temporal AA or a saved native material. Their improvement over the repetitive source garden forms is a promising shape direction, not scene acceptance. The original R16 garden PNG still shows repeated broadleaf clusters, uniform lawn/bed boundaries and generated flower shapes.

Source geometry/byte/mask inspection and five CPU guard cases pass. Native, appearance, full photorealism, performance and Shipping acceptance remain false. Native preparation must consume a separately pinned actual saved R22 base and preserve the full original actor/material/texture witness; no layout, camera, light, collision or architecture change is authorized by this source study.

Source plan: `output/unreal/exterior-garden-fern-20261002-r25-study/fern-pilot-source-plan.json`.

Original resources: `output/unreal/exterior-ph-fern-reference-20261002-r1/`.

CPU previews: `output/unreal/exterior-garden-fern-20261002-r25-source-review/`.
