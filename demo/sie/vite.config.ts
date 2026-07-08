import {defineConfig} from 'vite';
import motionCanvasPlugin from '@motion-canvas/vite-plugin';

// Handle both ESM and CJS interop shapes of the plugin's default export.
const motionCanvas =
  (motionCanvasPlugin as unknown as {default?: typeof motionCanvasPlugin})
    .default ?? motionCanvasPlugin;

export default defineConfig({
  plugins: [motionCanvas()],
});
