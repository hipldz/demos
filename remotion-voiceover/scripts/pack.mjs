import {mkdirSync} from 'node:fs';
import {execSync} from 'node:child_process';
mkdirSync(new URL('../build/', import.meta.url), {recursive: true});
execSync('npm pack --pack-destination build', {stdio: 'inherit'});
