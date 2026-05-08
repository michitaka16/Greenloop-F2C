// Generate custom curly-kale leaf PNGs in 5 colour variants
//
// Run:    node leaves.js
// Output: assets/leaf-*.png (5 files, ~70KB each)
//
// Only run this when you want to redesign the leaf shape or
// generate new colour variants. The leaf SVG itself is below.

const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const OUT_DIR = path.join(__dirname, "assets");
if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

// Curly kale leaf — frilly outer edge, central stem, side veins.
// viewBox 100×120 (leaves room for stem at bottom).
function leafSvg(fillColor, veinColor, strokeColor) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120">
    <line x1="50" y1="105" x2="50" y2="118" stroke="${strokeColor}" stroke-width="3" stroke-linecap="round"/>
    <path d="
      M 50 8
      Q 42 4 35 8 Q 27 6 22 12 Q 15 12 12 20 Q 6 22 6 30
      Q 2 35 6 42 Q 0 48 6 54 Q 2 62 8 66 Q 4 74 12 78
      Q 10 86 18 90 Q 16 96 26 98 Q 28 104 38 102 Q 42 106 50 104
      Q 58 106 62 102 Q 72 104 74 98 Q 84 96 82 90 Q 90 86 88 78
      Q 96 74 92 66 Q 98 62 94 54 Q 100 48 94 42 Q 98 35 94 30
      Q 94 22 88 20 Q 85 12 78 12 Q 73 6 65 8 Q 58 4 50 8 Z
    " fill="${fillColor}" stroke="${strokeColor}" stroke-width="0.8" stroke-linejoin="round"/>
    <line x1="50" y1="10" x2="50" y2="105" stroke="${veinColor}" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M 50 22 Q 35 22 22 28" stroke="${veinColor}" stroke-width="1" fill="none"/>
    <path d="M 50 22 Q 65 22 78 28" stroke="${veinColor}" stroke-width="1" fill="none"/>
    <path d="M 50 42 Q 28 44 12 50" stroke="${veinColor}" stroke-width="1" fill="none"/>
    <path d="M 50 42 Q 72 44 88 50" stroke="${veinColor}" stroke-width="1" fill="none"/>
    <path d="M 50 65 Q 26 66 10 70" stroke="${veinColor}" stroke-width="1" fill="none"/>
    <path d="M 50 65 Q 74 66 90 70" stroke="${veinColor}" stroke-width="1" fill="none"/>
    <path d="M 50 85 Q 30 86 18 90" stroke="${veinColor}" stroke-width="1" fill="none"/>
    <path d="M 50 85 Q 70 86 82 90" stroke="${veinColor}" stroke-width="1" fill="none"/>
  </svg>`;
}

// Outline-only leaf — for use on dark backgrounds (closing slide)
function leafOutlineSvg(strokeColor) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120">
    <line x1="50" y1="105" x2="50" y2="118" stroke="${strokeColor}" stroke-width="3" stroke-linecap="round"/>
    <path d="
      M 50 8
      Q 42 4 35 8 Q 27 6 22 12 Q 15 12 12 20 Q 6 22 6 30
      Q 2 35 6 42 Q 0 48 6 54 Q 2 62 8 66 Q 4 74 12 78
      Q 10 86 18 90 Q 16 96 26 98 Q 28 104 38 102 Q 42 106 50 104
      Q 58 106 62 102 Q 72 104 74 98 Q 84 96 82 90 Q 90 86 88 78
      Q 96 74 92 66 Q 98 62 94 54 Q 100 48 94 42 Q 98 35 94 30
      Q 94 22 88 20 Q 85 12 78 12 Q 73 6 65 8 Q 58 4 50 8 Z
    " fill="none" stroke="${strokeColor}" stroke-width="2" stroke-linejoin="round"/>
    <line x1="50" y1="10" x2="50" y2="105" stroke="${strokeColor}" stroke-width="1.6" stroke-linecap="round"/>
    <path d="M 50 22 Q 35 22 22 28" stroke="${strokeColor}" stroke-width="1" fill="none"/>
    <path d="M 50 22 Q 65 22 78 28" stroke="${strokeColor}" stroke-width="1" fill="none"/>
    <path d="M 50 42 Q 28 44 12 50" stroke="${strokeColor}" stroke-width="1" fill="none"/>
    <path d="M 50 42 Q 72 44 88 50" stroke="${strokeColor}" stroke-width="1" fill="none"/>
    <path d="M 50 65 Q 26 66 10 70" stroke="${strokeColor}" stroke-width="1" fill="none"/>
    <path d="M 50 65 Q 74 66 90 70" stroke="${strokeColor}" stroke-width="1" fill="none"/>
  </svg>`;
}

async function svgToPng(svg, outFile, size = 1000) {
  const buf = await sharp(Buffer.from(svg))
    .resize(size, Math.round(size * 1.2)) // 100×120 viewBox ratio
    .png()
    .toBuffer();
  fs.writeFileSync(path.join(OUT_DIR, outFile), buf);
  console.log("Wrote", path.join(OUT_DIR, outFile));
}

(async () => {
  await svgToPng(leafSvg("#2D5016", "#1A2F0D", "#1A2F0D"), "leaf-dark.png");
  await svgToPng(leafSvg("#7BA05B", "#2D5016", "#2D5016"), "leaf-mid.png");
  await svgToPng(leafSvg("#C7E66B", "#2D5016", "#2D5016"), "leaf-lime.png");
  await svgToPng(leafOutlineSvg("#C7E66B"),                 "leaf-outline-lime.png");
  await svgToPng(leafOutlineSvg("#7BA05B"),                 "leaf-outline-mid.png");
})();
