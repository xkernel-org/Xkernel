/**
 * Headless render entry (used by scripts/render.mjs via puppeteer).
 * Renders the project to an image sequence in output/ through the
 * vite plugin, without opening the editor UI.
 */
import {Renderer, Vector2} from '@motion-canvas/core';

// The `?project` query makes the vite plugin bootstrap a full Project
// (logger, meta, plugins) — a bare `./project` import is just the
// makeProject description and cannot be rendered.
import project from './project?project';

declare global {
  interface Window {
    __done: boolean;
    __error: string | null;
  }
}

window.__done = false;
window.__error = null;

const params = new URLSearchParams(location.search);
const fps = Number(params.get('fps') ?? 15);
const scale = Number(params.get('scale') ?? 0.5);
// optional scene-time window (seconds) for quick partial previews
const start = Number(params.get('start') ?? 0);
const end = Number(params.get('end') ?? Infinity);

(async () => {
  try {
    project.logger.onLogged.subscribe(log => console.log('[log]', log.message));
    const renderer = new Renderer(project);
    await renderer.render({
      ...project.meta.getFullRenderingSettings(),
      name: 'sie',
      fps,
      range: [start, end],
      resolutionScale: scale,
      size: new Vector2(1920, 1080),
      background: '#FFFFFF',
    });
    window.__done = true;
    console.log('RENDER_DONE');
  } catch (e) {
    window.__error = String(e);
    console.error('RENDER_ERROR', e);
  }
})();
