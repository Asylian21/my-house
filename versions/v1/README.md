# Historical `/v1` route

This route preserves the `v1` branch at commit
`1057ed30e7a3d5b63a938acf47208ae1f3f296af` (4 September 2026).
Creating or pushing a Git branch does not create a URL on Sites; the route is
included in the main site's deployment through `app/v1/page.tsx`.

The original application modules, stylesheet, and assets are checked in here
and under `public/v1-assets`. Their imports and asset URLs use the snapshot's
namespace so later changes to the main model do not change the historical model.
The shared root layout supplies the original document language, fonts and metadata.
Each page loads its own stylesheet. Package versions remain shared with the site.

`snapshot.json` records the original commit and SHA-256 of every source file and
asset. `node scripts/snapshot-v1.mjs` recreates these files from the pinned commit
when its Git object is available. Do not edit the generated files to update the
current house; make those changes in the main `app` and `lib` directories.
