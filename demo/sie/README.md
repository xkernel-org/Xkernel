# SIE Animation (Motion Canvas)

Animated explanation of Scoped Indirect Execution (SIE) from the Xkernel paper
(arXiv:2512.12530), in the visual style of the May 5th talk slides.

## Storyline

1. Source `#define V 5` compiles into the binary.
2. Symbolic execution from a seed instruction walks the instructions and
   combines them (`eax = x` → `eax = x*V` → `eax = x*V*2`) into the
   symbolic state expression `eax ← eax * V * 2`.
3. The expression pins down the critical span (CS, purple) — scope for the
   value update.
4. A second scope in another color: the safe span (SS, teal dashed) — scope
   for *enabling* the update.
5. `x_set(V′ = 10)`: the expression is pasted into the indirection
   `{address, update}` and reversed into
   `eax = (eax / (V*2)) * V′ * 2` — attached at the CS edge, labeled OFF.
6. The PC runs with the indirection OFF (old behavior, eax = 30); when it
   exits the SS boundary (flash) → no side effects → toggle flips to ON.
7. Next entry: the PC hits the indirection, the synthesized code executes,
   `eax: 30 → 3 → 60` — as if V′ had been compiled in.
8. Finale: the tuning policy plane — per-PID / per-device values
   (HDD → 128, NVMe → 1), everything else unchanged.

## Usage

```bash
npm install
npm start        # editor at http://localhost:9000
```

Render from the editor (Render button): 1920×1080, 60 fps, image sequence or
video. Total length ≈ 45 s.

Scene source: `src/scenes/sie.tsx` (single continuous scene; colors and
layout constants at the top of the file).
