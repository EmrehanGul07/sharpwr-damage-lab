# Original terrain surface assets v1

Created with the built-in imagegen tool on 9 October 2026 for SharpWR. Four 627×627 WebP albedo maps, lossily encoded at quality 92, packed from one generated 1254×1254 atlas. Total payload approximately 575 KiB. Original generated art, no Riot textures or extracted game assets. The generated atlas is split only for runtime material sampling.

Prompt: One production square texture atlas with four equal quadrants, no borders, text or logos. Flat orthographic hand-painted mobile MOBA albedo surfaces: upper-left weathered warm gray limestone with mineral detail and cracks; upper-right muted emerald/sage meadow grass; lower-left cool blue-gray slate with worn striations and moss flecks; lower-right dark teal/sage pine needles and evergreen foliage. Edge-to-edge repeatable surfaces, no perspective, cast shadows or standing objects, premium Wild Rift-like surface detail, original artwork.

Runtime: stone-v1.webp for paving, grass-v1.webp for ground, rock-v1.webp for cliffs and wall, foliage-v1.webp for pines and curved brush cards. Separate material caches keep paving maps out of foliage/rock. Mipmaps, anisotropy 4 and world-based ground UVs control oblique sampling. The four images ship locally in the Android web bundle; web views use Streamlit static assets.

627px is the native quadrant resolution, not a 2K texture; do not describe these assets as 2K/4K. These are detailed original surfaces, not exact Riot art.
