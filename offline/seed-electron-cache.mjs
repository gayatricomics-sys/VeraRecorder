// Copies an Electron runtime zip into the cache layout that @electron/get
// (used by `node_modules/electron` on first launch) reads, so `npm run dev`
// starts without downloading Electron.
//
// Usage: node offline/seed-electron-cache.mjs <electron dir> <zip> <cache dir> <platform> <arch>
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [electronDir, zipPath, cacheRoot, platform, arch] = process.argv.slice(2);
const getDir = path.join(electronDir, 'node_modules', '@electron', 'get', 'dist');
const { Cache } = await import(pathToFileURL(path.join(getDir, 'Cache.js')).href);
const { getArtifactRemoteURL, getArtifactFileName } = await import(pathToFileURL(path.join(getDir, 'artifact-utils.js')).href);

const version = JSON.parse(fs.readFileSync(path.join(electronDir, 'node_modules', 'electron', 'package.json'), 'utf8')).version;
// @electron/get normalizes versions to a leading "v" before building URLs.
const details = { version: version.startsWith('v') ? version : `v${version}`, artifactName: 'electron', platform, arch, isGeneric: false, mirrorOptions: {} };
const url = await getArtifactRemoteURL(details);
const fileName = getArtifactFileName(details);
const dest = new Cache(path.resolve(cacheRoot)).getCachePath(url, fileName);

fs.mkdirSync(path.dirname(dest), { recursive: true });
fs.copyFileSync(zipPath, dest);
console.log(`  seeded ${fileName} -> ${path.relative(process.cwd(), dest)}`);
