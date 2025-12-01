import { copyFileSync, existsSync } from 'fs';
import { join } from 'path';

// Cross-platform small script to copy static.json into dist/
const root = process.cwd();
const src = join(root, 'static.json');
const destDir = join(root, 'dist');
const dest = join(destDir, 'static.json');

if (!existsSync(src)) {
  console.error('copy_static.js: source static.json not found at', src);
  process.exit(1);
}

try {
  copyFileSync(src, dest);
  console.log('copy_static.js: copied', src, '->', dest);
} catch (err) {
  console.error('copy_static.js: failed to copy static.json:', err);
  process.exit(1);
}
