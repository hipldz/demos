import {copyFileSync} from 'node:fs';
copyFileSync(new URL('../src/react/voice.css', import.meta.url), new URL('../dist/voice.css', import.meta.url));
