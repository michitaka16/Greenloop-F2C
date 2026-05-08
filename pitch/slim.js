// Slim — deduplicate identical images inside the generated .pptx
//
// Why:    pptxgenjs embeds the same image bytes once per addImage() call.
//         Our 5 leaf PNGs get duplicated ~18 times → 1.5MB file.
//         This script SHA-256 hashes them, keeps one copy, and rewrites
//         every slide's _rels XML to point at the canonical filename.
//
// Run:    node slim.js
// Input:  output/AdoptAKale.pptx
// Output: output/AdoptAKale.pptx (overwritten, slimmed)
//
// Result: ~1.5MB → ~290KB (Claude.ai preview also stops failing).

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { execSync } = require("child_process");

const SRC = path.join(__dirname, "output", "AdoptAKale.pptx");
const TMP = path.join(__dirname, ".slim-tmp");

if (!fs.existsSync(SRC)) {
  console.error(`Not found: ${SRC}\nRun \`node build.js\` first.`);
  process.exit(1);
}

// Clean tmp
fs.rmSync(TMP, { recursive: true, force: true });
fs.mkdirSync(TMP, { recursive: true });

// Unzip
execSync(`cd "${TMP}" && unzip -q "${SRC}"`);

// Hash media files, build dedup map
const mediaDir = path.join(TMP, "ppt/media");
const hashToCanonical = {};
const fileToCanonical = {};
for (const fn of fs.readdirSync(mediaDir).sort()) {
  const full = path.join(mediaDir, fn);
  if (!fs.statSync(full).isFile()) continue;
  const h = crypto.createHash("sha256").update(fs.readFileSync(full)).digest("hex");
  if (!(h in hashToCanonical)) {
    hashToCanonical[h] = fn;
    fileToCanonical[fn] = fn;
  } else {
    fileToCanonical[fn] = hashToCanonical[h];
  }
}

const removed = Object.entries(fileToCanonical).filter(([fn, can]) => fn !== can);
console.log(`Will deduplicate ${removed.length} of ${Object.keys(fileToCanonical).length} media files`);

// Rewrite slide _rels to point duplicates at canonical
const relsDir = path.join(TMP, "ppt/slides/_rels");
for (const relsFn of fs.readdirSync(relsDir)) {
  const p = path.join(relsDir, relsFn);
  let xml = fs.readFileSync(p, "utf-8");
  let changed = false;
  for (const [fn, canonical] of Object.entries(fileToCanonical)) {
    if (fn === canonical) continue;
    const before = xml;
    xml = xml.replace(new RegExp(`\\.\\./media/${fn}`, "g"), `../media/${canonical}`);
    if (xml !== before) changed = true;
  }
  if (changed) fs.writeFileSync(p, xml);
}

// Remove duplicate files from media/
for (const [fn, canonical] of Object.entries(fileToCanonical)) {
  if (fn === canonical) continue;
  try { fs.unlinkSync(path.join(mediaDir, fn)); } catch {}
}

// Re-zip
const out = SRC + ".tmp";
fs.rmSync(out, { force: true });
execSync(`cd "${TMP}" && zip -qr "${out}" .`);
fs.renameSync(out, SRC);
fs.rmSync(TMP, { recursive: true, force: true });

const sizeKB = Math.round(fs.statSync(SRC).size / 1024);
console.log(`Slimmed: ${SRC} (${sizeKB} KB)`);
