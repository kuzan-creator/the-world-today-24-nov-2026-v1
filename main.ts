// The World in One Day — Tuesday 24 November 2026: 35 stories (v1).
// Entrypoint: copy the pre-generated entry.png to the output dir.
// No dependencies, no network, deterministic: the output bytes are
// exactly the bytes of the image the repository holds.
//
// Usage:  node main.ts
// Writes: <MAKEFUN_OUTPUT_DIR | OUTPUT_DIR | /output>/entry.png
import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "entry.png");
if (!existsSync(src)) {
  console.error(`missing ${src}`);
  process.exit(1);
}
const srcBytes = readFileSync(src);
const pngMagic = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
if (!srcBytes.subarray(0, 8).equals(pngMagic)) {
  console.error("entry.png is not a PNG file");
  process.exit(1);
}
const outDir =
  process.env.MAKEFUN_OUTPUT_DIR || process.env.OUTPUT_DIR || "/output";
mkdirSync(outDir, { recursive: true });
const dst = join(outDir, "entry.png");
copyFileSync(src, dst);
const bytes = readFileSync(dst);
if (!bytes.equals(srcBytes)) {
  console.error("copy mismatch: output differs from entry.png");
  process.exit(1);
}
const sha = createHash("sha256").update(bytes).digest("hex");
console.log(`wrote ${dst}  1024x1024  ${bytes.length} bytes  sha256=${sha}`);
console.log("stories: 35");
