import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {defineConfig} from 'vite';
import {voiceoverPlugin} from '../src/server/index.js';
import {exampleProject} from './project.js';

const projectRoot = fileURLToPath(new URL('..', import.meta.url));

// Add this plugin alongside the consuming project's existing Vite plugins.
export default defineConfig({
  root: resolve(projectRoot, 'examples'),
  publicDir: resolve(projectRoot, 'public'),
  plugins: [voiceoverPlugin({project: exampleProject, projectRoot})],
  server: {host: '127.0.0.1', fs: {allow: [projectRoot]}},
  build: {outDir: resolve(projectRoot, 'build/example'), emptyOutDir: true},
});
