import {makeScene2D, Circle, Line, Node, Rect, Txt} from '@motion-canvas/2d';
import {
  all,
  createRef,
  createSignal,
  easeInOutCubic,
  easeOutBack,
  makeRef,
  sequence,
  waitFor,
} from '@motion-canvas/core';

// ============================================================
// Palette (matched to the Talk-Xkernel slides)
// ============================================================
const MONO = 'JetBrains Mono, Menlo, Consolas, monospace';
const SANS = 'Inter, Helvetica Neue, Segoe UI, Arial, sans-serif';
const INK = '#1A1A1A';
const GRAY = '#8A8A8A';
const RED = '#B85450'; // asm text / "reverse" part
const PURPLE = '#7030A0'; // CS scope, symbolic expression
const PURPLE_LT = '#B18CD9'; // derive arrows
const TEAL = '#1F8A70'; // SS scope (the *other* colored scope)
const TEAL_FILL = '#E2F2EE';
const BLUE = '#2E75B6'; // indirection
const BLUE_FILL = '#DEEBF7';
const CREAM = '#FDF5E1'; // binary box
const GREEN = '#2E9E4F';

// ============================================================
// The example program:  int scale(int x) { y = 2*V*x; return y > 200; }
// V = 5  →  eax = 10·x.  With input x = 3: eax = 30.
// ============================================================
const INSTRS = [
  'mov  $0x8,0x170(%rbx)',
  'add  $0x1,%ebx',
  'shl  $0x2,%ebx',
  'mov  0x4(%rsp),%eax', // CS ─ seed: eax = x
  'xor  %ecx,%ecx', //      (V-irrelevant)
  'lea  (%rax,%rax,4),%eax', // CS: eax = x*5
  'add  %eax,%eax', // CS: eax = x*5*2
  'cmp  $0xc8,%eax', // return y > 200
];
const CS_ROWS = [3, 5, 6];

// ============================================================
// Geometry
// ============================================================
const ROW_H = 56;
const BOX_W = 470;
const BOX_X = -260;
const BOX_Y = -70;
const BOX_H = INSTRS.length * ROW_H + 40;
const boxTop = BOX_Y - BOX_H / 2;
const boxBottom = BOX_Y + BOX_H / 2;
const boxLeft = BOX_X - BOX_W / 2;
const boxRight = BOX_X + BOX_W / 2;
const rowY = (i: number) => boxTop + 20 + ROW_H / 2 + i * ROW_H;

// Critical span (CS): rows 3..6 — where V enters runtime states (registers, memory).
const CS_TOP = rowY(3) - ROW_H / 2;
const CS_BOT = rowY(6) + ROW_H / 2;
const CS_MID = (CS_TOP + CS_BOT) / 2;
// Safe span (SS): rows 1..7 — side-effect-free scope for ENABLING the update.
const SS_TOP = rowY(1) - ROW_H / 2;
const SS_BOT = rowY(7) + ROW_H / 2;

// Indirection box.
const IND_X = 620;
const IND_Y = 40;
const IND_W = 600;
const IND_H = 250;

export default makeScene2D(function* (view) {
  view.fill('#FFFFFF');

  const eaxVal = createSignal('—');

  // ---------- refs ----------
  const title = createRef<Txt>();
  const caption = createRef<Txt>();
  const mainGrp = createRef<Node>();
  const srcGrp = createRef<Node>();
  const asmGrp = createRef<Node>();
  const vNew = createRef<Txt>();
  const ssBand = createRef<Rect>();
  const csBand = createRef<Rect>();
  const bar = createRef<Rect>();
  const csBracket = createRef<Line>();
  const csLabel = createRef<Txt>();
  const ssBracket = createRef<Line>();
  const ssLabel = createRef<Txt>();
  const ssExitLine = createRef<Line>();
  const ssExitTag = createRef<Txt>();
  const seedMark = createRef<Rect>();
  const seedLabel = createRef<Txt>();
  const symCursor = createRef<Node>();
  const symHead = createRef<Txt>();
  const st1 = createRef<Txt>();
  const stIr = createRef<Txt>();
  const st2 = createRef<Txt>();
  const st3 = createRef<Txt>();
  const symCard = createRef<Node>();
  const exprClone = createRef<Txt>();
  const reqGrp = createRef<Node>();
  const indGrp = createRef<Node>();
  const toggleBg = createRef<Rect>();
  const toggleTxt = createRef<Txt>();
  const seg1 = createRef<Txt>();
  const seg2 = createRef<Txt>();
  const seg3 = createRef<Txt>();
  const labRev = createRef<Txt>();
  const labApp = createRef<Txt>();
  const trigDot = createRef<Circle>();
  const trigRing = createRef<Circle>();
  const transArrow = createRef<Line>();
  const retArrow = createRef<Line>();
  const dot = createRef<Circle>();
  const pc = createRef<Node>();
  const pcLabel = createRef<Txt>();
  const eaxGrp = createRef<Node>();
  const eaxBox = createRef<Rect>();
  const check = createRef<Txt>();
  const policyGrp = createRef<Node>();

  const rowTxts: Txt[] = [];
  const csRects: Rect[] = [];
  const links: Line[] = [];

  view.add(
    <>
      {/* ========== title & caption (always on top level) ========== */}
      <Txt
        ref={title}
        text={'Scoped Indirect Execution (SIE)'}
        fontFamily={SANS}
        fontSize={54}
        fontWeight={600}
        fill={INK}
        offset={[-1, 0]}
        position={[-890, -470]}
        opacity={0}
      />
      <Txt
        ref={caption}
        text={''}
        fontFamily={SANS}
        fontSize={37}
        fontWeight={500}
        fill={INK}
        position={[0, 418]}
        opacity={0}
      />

      {/* ================= main diagram ================= */}
      <Node ref={mainGrp}>
        {/* ---------- source code ---------- */}
        <Node ref={srcGrp} opacity={0}>
          <Txt text={'source code'} fontFamily={SANS} fontSize={24} fill={GRAY} position={[-785, -246]} />
          <Rect
            width={360}
            height={250}
            position={[-785, -90]}
            fill={'#FFFFFF'}
            stroke={'#BFBFBF'}
            lineWidth={2}
            radius={6}
            shadowColor={'#00000022'}
            shadowBlur={12}
            shadowOffset={[2, 3]}
          />
          <Txt text={'#define V 5'} fontFamily={MONO} fontSize={24} fill={RED} offset={[-1, 0]} position={[-945, -180]} />
          <Txt text={'int scale(int x) {'} fontFamily={MONO} fontSize={24} fill={INK} offset={[-1, 0]} position={[-945, -110]} />
          <Txt text={'  int y = 2*V*x;'} fontFamily={MONO} fontSize={24} fill={INK} offset={[-1, 0]} position={[-945, -75]} />
          <Txt text={'  return y > 200;'} fontFamily={MONO} fontSize={24} fill={INK} offset={[-1, 0]} position={[-945, -40]} />
          <Txt text={'}'} fontFamily={MONO} fontSize={24} fill={INK} offset={[-1, 0]} position={[-945, -5]} />
          <Txt
            ref={vNew}
            text={'→ 10'}
            fontFamily={MONO}
            fontSize={24}
            fontWeight={700}
            fill={BLUE}
            offset={[-1, 0]}
            position={[-780, -180]}
            opacity={0}
          />
        </Node>

        {/* ---------- binary box ---------- */}
        <Node ref={asmGrp} opacity={0}>
          <Txt text={'binary'} fontFamily={SANS} fontSize={24} fill={GRAY} position={[BOX_X, boxTop - 26]} />
          <Rect
            width={BOX_W}
            height={BOX_H}
            position={[BOX_X, BOX_Y]}
            fill={CREAM}
            stroke={'#E4D7B0'}
            lineWidth={2}
            radius={6}
          />
        </Node>

        {/* scope bands + current-row bar + CS highlights (behind text) */}
        <Rect
          ref={ssBand}
          width={BOX_W - 4}
          height={SS_BOT - SS_TOP}
          position={[BOX_X, (SS_TOP + SS_BOT) / 2]}
          fill={TEAL_FILL}
          radius={4}
          opacity={0}
        />
        <Rect
          ref={csBand}
          width={BOX_W - 12}
          height={CS_BOT - CS_TOP}
          position={[BOX_X, CS_MID]}
          fill={'#EFE6F7'}
          radius={4}
          opacity={0}
        />
        <Rect
          ref={bar}
          width={BOX_W - 18}
          height={ROW_H - 8}
          position={[BOX_X, rowY(0)]}
          fill={'#0000000D'}
          radius={4}
          opacity={0}
        />
        {CS_ROWS.map((r, k) => (
          <Rect
            ref={makeRef(csRects, k)}
            width={BOX_W - 28}
            height={ROW_H - 12}
            position={[BOX_X, rowY(r)]}
            fill={'#DCDCDC'}
            stroke={'#9E9E9E'}
            lineWidth={2}
            radius={4}
            opacity={0}
          />
        ))}
        {INSTRS.map((t, i) => (
          <Txt
            ref={makeRef(rowTxts, i)}
            text={t}
            fontFamily={MONO}
            fontSize={27}
            fill={RED}
            offset={[-1, 0]}
            position={[boxLeft + 26, rowY(i)]}
            opacity={0}
          />
        ))}

        {/* source -> CS connector lines (compile step) */}
        {CS_ROWS.map((r, k) => (
          <Line
            ref={makeRef(links, k)}
            points={[
              [-605, -75],
              [boxLeft - 4, rowY(r)],
            ]}
            stroke={'#9E9E9E'}
            lineWidth={2}
            end={0}
          />
        ))}

        {/* ---------- CS bracket (purple, solid) ---------- */}
        <Line
          ref={csBracket}
          points={[
            [boxRight + 12, CS_TOP],
            [boxRight + 28, CS_TOP],
            [boxRight + 28, CS_BOT],
            [boxRight + 12, CS_BOT],
          ]}
          stroke={PURPLE}
          lineWidth={5}
          radius={6}
          end={0}
        />
        <Txt
          ref={csLabel}
          text={'Critical span (CS)\nscope for the value update'}
          fontFamily={SANS}
          fontSize={26}
          fontWeight={700}
          fill={PURPLE}
          textAlign={'center'}
          position={[170, CS_MID - 120]}
          opacity={0}
        />

        {/* ---------- SS bracket (teal, dashed — the *other* scope) ---------- */}
        <Line
          ref={ssBracket}
          points={[
            [boxRight + 44, SS_TOP],
            [boxRight + 60, SS_TOP],
            [boxRight + 60, SS_BOT],
            [boxRight + 44, SS_BOT],
          ]}
          stroke={TEAL}
          lineWidth={5}
          lineDash={[14, 10]}
          radius={6}
          end={0}
        />
        <Txt
          ref={ssLabel}
          text={'Safe span (SS)\nscope for enabling the update'}
          fontFamily={SANS}
          fontSize={26}
          fontWeight={700}
          fill={TEAL}
          textAlign={'center'}
          position={[130, SS_BOT + 64]}
          opacity={0}
        />
        {/* SS exit boundary (flashes when the PC leaves the SS) */}
        <Line
          ref={ssExitLine}
          points={[
            [boxLeft - 12, SS_BOT],
            [boxRight + 64, SS_BOT],
          ]}
          stroke={TEAL}
          lineWidth={4}
          lineDash={[10, 8]}
          opacity={0}
        />
        <Txt
          ref={ssExitTag}
          text={'exit — no side effects'}
          fontFamily={SANS}
          fontSize={24}
          fontStyle={'italic'}
          fill={TEAL}
          position={[-570, SS_BOT]}
          opacity={0}
        />

        {/* ---------- symbolic execution panel ---------- */}
        <Rect ref={seedMark} size={16} rotation={45} fill={PURPLE} position={[boxLeft - 14, rowY(3)]} opacity={0} />
        <Txt
          ref={seedLabel}
          text={'seed instruction'}
          fontFamily={SANS}
          fontSize={22}
          fontStyle={'italic'}
          fill={PURPLE}
          position={[-645, rowY(3) - 36]}
          opacity={0}
        />
        <Txt
          ref={symHead}
          text={'symbolic execution ▾'}
          fontFamily={SANS}
          fontSize={26}
          fontStyle={'italic'}
          fill={PURPLE}
          offset={[-1, 0]}
          position={[40, rowY(3) - 60]}
          opacity={0}
        />
        <Txt ref={st1} text={'eax = x'} fontFamily={MONO} fontSize={28} fill={PURPLE} offset={[-1, 0]} position={[40, rowY(3)]} opacity={0} />
        <Txt ref={stIr} text={'(V-irrelevant, skipped)'} fontFamily={SANS} fontSize={22} fill={GRAY} offset={[-1, 0]} position={[40, rowY(4)]} opacity={0} />
        <Txt ref={st2} text={'eax = x * 5'} fontFamily={MONO} fontSize={28} fill={PURPLE} offset={[-1, 0]} position={[40, rowY(5)]} opacity={0} />
        <Txt ref={st3} text={'eax = x * V * 2'} fontFamily={MONO} fontSize={28} fill={PURPLE} offset={[-1, 0]} position={[40, rowY(6)]} opacity={0} />

        {/* purple hollow cursor used by the symbolic executor */}
        <Node ref={symCursor} position={[boxLeft - 40, rowY(3)]} opacity={0}>
          <Line points={[[-13, -14], [13, 0], [-13, 14]]} closed stroke={PURPLE} lineWidth={4} fill={'#F5EEFB'} />
        </Node>

        {/* combined result: the symbolic state expression */}
        <Node ref={symCard} opacity={0}>
          <Txt
            text={'eax ← eax * V * 2'}
            fontFamily={MONO}
            fontSize={34}
            fontWeight={700}
            fill={PURPLE}
            position={[BOX_X, 258]}
          />
          <Txt
            text={'Symbolic state expression — how V enters runtime states (registers, memory)'}
            fontFamily={SANS}
            fontSize={24}
            fill={PURPLE}
            position={[BOX_X, 306]}
          />
        </Node>

        {/* clone that gets "pasted" into the indirection */}
        <Txt
          ref={exprClone}
          text={'eax ← eax * V * 2'}
          fontFamily={MONO}
          fontSize={30}
          fontWeight={600}
          fill={PURPLE}
          position={[BOX_X, 258]}
          opacity={0}
        />

        {/* ---------- tuning request ---------- */}
        <Node ref={reqGrp} position={[IND_X, -390]} opacity={0} scale={0.7}>
          <Rect width={380} height={84} fill={'#F5EEFB'} stroke={PURPLE} lineWidth={3} radius={12} />
          <Txt text={'x_set(V′ = 10)'} fontFamily={MONO} fontSize={30} fontWeight={700} fill={PURPLE} />
          <Txt text={'tuning request'} fontFamily={SANS} fontSize={22} fill={GRAY} position={[0, 62]} />
        </Node>

        {/* ---------- the indirection ---------- */}
        <Node ref={indGrp} opacity={0} x={40}>
          <Txt
            text={'An Indirection'}
            fontFamily={SANS}
            fontSize={34}
            fontWeight={700}
            fill={PURPLE}
            position={[IND_X, -130]}
          />
          <Rect
            width={IND_W}
            height={IND_H}
            position={[IND_X, IND_Y]}
            fill={BLUE_FILL}
            stroke={BLUE}
            lineWidth={3}
            radius={10}
          />
          <Txt text={'{address, update}'} fontFamily={MONO} fontSize={26} fill={'#5B7FA6'} position={[IND_X, -45]} />
          {/* OFF / ON toggle chip on the box border */}
          <Rect ref={toggleBg} width={96} height={44} radius={22} position={[850, IND_Y - IND_H / 2]} fill={'#9E9E9E'} />
          <Txt
            ref={toggleTxt}
            text={'OFF'}
            fontFamily={SANS}
            fontSize={24}
            fontWeight={700}
            fill={'#FFFFFF'}
            position={[850, IND_Y - IND_H / 2]}
          />
        </Node>
        {/* synthesized update, colored: reverse (red) + apply (blue) */}
        <Txt ref={seg1} text={'eax = '} fontFamily={MONO} fontSize={30} fontWeight={600} fill={INK} offset={[-1, 0]} position={[368, 25]} opacity={0} />
        <Txt ref={seg2} text={'(eax / (V*2))'} fontFamily={MONO} fontSize={30} fontWeight={600} fill={RED} offset={[-1, 0]} position={[476, 25]} opacity={0} />
        <Txt ref={seg3} text={' * V′ * 2'} fontFamily={MONO} fontSize={30} fontWeight={600} fill={BLUE} offset={[-1, 0]} position={[710, 25]} opacity={0} />
        <Txt ref={labRev} text={'reverse V'} fontFamily={SANS} fontSize={22} fontStyle={'italic'} fill={RED} position={[593, 74]} opacity={0} />
        <Txt ref={labApp} text={'apply V′'} fontFamily={SANS} fontSize={22} fontStyle={'italic'} fill={BLUE} position={[791, 74]} opacity={0} />

        {/* ---------- control transfer ---------- */}
        <Line
          ref={transArrow}
          points={[
            [boxRight + 10, rowY(6)],
            [IND_X - IND_W / 2 - 16, rowY(6)],
          ]}
          stroke={BLUE}
          lineWidth={7}
          endArrow
          arrowSize={16}
          end={0}
        />
        <Line
          ref={retArrow}
          points={[
            [IND_X - IND_W / 2 + 30, IND_Y + IND_H / 2 + 8],
            [80, IND_Y + IND_H / 2 + 8],
            [boxRight + 12, rowY(7) + 6],
          ]}
          radius={24}
          stroke={BLUE}
          lineWidth={5}
          lineDash={[12, 10]}
          endArrow
          arrowSize={14}
          end={0}
        />
        <Circle ref={trigRing} size={18} stroke={BLUE} lineWidth={4} position={[boxRight, rowY(6)]} opacity={0} />
        <Circle ref={trigDot} size={18} fill={BLUE} position={[boxRight, rowY(6)]} scale={0} />
        <Circle ref={dot} size={20} fill={BLUE} position={[boxRight, rowY(6)]} opacity={0} />

        {/* ---------- program counter ---------- */}
        <Txt
          ref={pcLabel}
          text={'Program\nCounter'}
          fontFamily={SANS}
          fontSize={21}
          fill={INK}
          textAlign={'center'}
          position={[-608, rowY(2)]}
          opacity={0}
        />
        <Node ref={pc} position={[boxLeft - 40, rowY(0)]} opacity={0}>
          <Line points={[[-13, -14], [13, 0], [-13, 14]]} closed fill={INK} />
        </Node>

        {/* ---------- eax readout ---------- */}
        <Node ref={eaxGrp} opacity={0}>
          <Rect
            ref={eaxBox}
            width={320}
            height={76}
            position={[-785, 200]}
            fill={'#F7F7F7'}
            stroke={'#BBBBBB'}
            lineWidth={2}
            radius={10}
          />
          <Txt
            text={() => `eax = ${eaxVal()}`}
            fontFamily={MONO}
            fontSize={30}
            fontWeight={600}
            fill={INK}
            position={[-785, 200]}
          />
          <Txt text={'input x = 3'} fontFamily={SANS} fontSize={22} fill={GRAY} position={[-785, 262]} />
        </Node>
        <Txt
          ref={check}
          text={'✓'}
          fontFamily={SANS}
          fontSize={52}
          fontWeight={700}
          fill={GREEN}
          position={[-596, 200]}
          opacity={0}
        />
      </Node>

      {/* ================= finale: tuning policy plane ================= */}
      <Node ref={policyGrp} opacity={0} scale={0.96}>
        <Txt
          text={'Tuning Policy Plane'}
          fontFamily={SANS}
          fontSize={46}
          fontWeight={700}
          fill={PURPLE}
          position={[0, -330]}
        />
        <Txt text={'$ x-load tuning-program'} fontFamily={MONO} fontSize={26} fill={GRAY} position={[0, -268]} />
        {/* policy code */}
        <Rect width={800} height={150} position={[0, -130]} fill={'#F5EEFB'} stroke={PURPLE} lineWidth={3} radius={12} />
        <Txt
          text={'if (pid == 1234 && HDD())      x_set(128);'}
          fontFamily={MONO}
          fontSize={27}
          fill={INK}
          offset={[-1, 0]}
          position={[-370, -160]}
        />
        <Txt
          text={'if (random_access() && NVMe()) x_set(1);'}
          fontFamily={MONO}
          fontSize={27}
          fill={INK}
          offset={[-1, 0]}
          position={[-370, -105]}
        />
        {/* arrows to targets */}
        <Line points={[[-260, -50], [-420, 90]]} stroke={PURPLE} lineWidth={4} endArrow arrowSize={13} />
        <Line points={[[0, -50], [0, 90]]} stroke={PURPLE} lineWidth={4} endArrow arrowSize={13} />
        <Line points={[[260, -50], [420, 90]]} stroke={'#B0B0B0'} lineWidth={4} endArrow arrowSize={13} />
        {/* targets */}
        <Rect width={260} height={84} position={[-420, 140]} fill={CREAM} stroke={'#C9BC94'} lineWidth={2} radius={10} />
        <Txt text={'HDD'} fontFamily={SANS} fontSize={30} fontWeight={700} fill={INK} position={[-420, 140]} />
        <Rect width={260} height={84} position={[0, 140]} fill={CREAM} stroke={'#C9BC94'} lineWidth={2} radius={10} />
        <Txt text={'NVMe SSD'} fontFamily={SANS} fontSize={30} fontWeight={700} fill={INK} position={[0, 140]} />
        <Rect width={300} height={84} position={[420, 140]} fill={'#F2F2F2'} stroke={'#BBBBBB'} lineWidth={2} radius={10} />
        <Txt text={'other PIDs / devices'} fontFamily={SANS} fontSize={24} fill={GRAY} position={[420, 140]} />
        {/* value badges */}
        <Rect width={230} height={76} position={[-420, 256]} fill={'#E3D5F1'} stroke={PURPLE} lineWidth={3} radius={14} />
        <Txt text={'128'} fontFamily={SANS} fontSize={34} fontWeight={700} fill={PURPLE} position={[-420, 244]} />
        <Txt text={'used at runtime'} fontFamily={SANS} fontSize={19} fill={PURPLE} position={[-420, 276]} />
        <Rect width={230} height={76} position={[0, 256]} fill={'#E3D5F1'} stroke={PURPLE} lineWidth={3} radius={14} />
        <Txt text={'1'} fontFamily={SANS} fontSize={34} fontWeight={700} fill={PURPLE} position={[0, 244]} />
        <Txt text={'used at runtime'} fontFamily={SANS} fontSize={19} fill={PURPLE} position={[0, 276]} />
        <Rect width={230} height={76} position={[420, 256]} fill={'#EFEFEF'} stroke={'#999999'} lineWidth={3} radius={14} />
        <Txt text={'default V'} fontFamily={SANS} fontSize={30} fontWeight={700} fill={GRAY} position={[420, 244]} />
        <Txt text={'unchanged'} fontFamily={SANS} fontSize={19} fill={GRAY} position={[420, 276]} />
      </Node>
    </>,
  );

  // ============================================================
  // Helpers
  // ============================================================
  function* setCaption(t: string) {
    yield* caption().opacity(0, 0.2);
    caption().text(t);
    yield* caption().opacity(1, 0.3);
  }

  /** Values eax takes after executing each row (input x = 3, V = 5). */
  const eaxAt: Record<number, string> = {3: '3', 5: '15', 6: '30'};

  /** Step the (black) program counter onto row i and apply its effect. */
  function* runRow(i: number, d = 0.45) {
    yield* all(
      pc().position.y(rowY(i), d, easeInOutCubic),
      bar().position.y(rowY(i), d, easeInOutCubic),
    );
    if (eaxAt[i] !== undefined) {
      eaxVal(eaxAt[i]);
      yield* eaxBox().scale(1.08, 0.12).to(1, 0.12);
    }
  }

  function* setEax(v: string) {
    eaxVal(v);
    yield* eaxBox().scale(1.12, 0.15).to(1, 0.15);
  }

  function* pulseRing() {
    trigRing().scale(1).opacity(0.9);
    yield* all(trigRing().scale(3.4, 0.55), trigRing().opacity(0, 0.55));
  }

  /** Flash a node's opacity n times (used for the ON chip / SS boundary). */
  function* flash(node: Node, n = 2) {
    for (let k = 0; k < n; k++) {
      yield* node.opacity(0.15, 0.16).to(1, 0.16);
    }
  }

  // ============================================================
  // Phase 1 — V is compiled into the binary
  // ============================================================
  yield* all(title().opacity(1, 0.5), srcGrp().opacity(1, 0.6), asmGrp().opacity(1, 0.6));
  yield* sequence(0.06, ...rowTxts.map(r => r.opacity(1, 0.25)));
  yield* sequence(0.12, ...links.map(l => l.end(1, 0.3)));
  yield* setCaption('A perf-const V = 5 is compiled into the kernel binary');
  yield* waitFor(1);

  // ============================================================
  // Phase 2 — symbolic execution recovers the math expression
  // ============================================================
  yield* all(...links.map(l => l.opacity(0.25, 0.4)));
  yield* all(seedMark().opacity(1, 0.35), seedLabel().opacity(1, 0.35));
  yield* setCaption('Start from a seed instruction and symbolically execute downwards');
  yield* all(symCursor().opacity(1, 0.3), symHead().opacity(1, 0.3));

  // row 3: eax = x
  yield* st1().opacity(1, 0.35);
  yield* waitFor(0.4);
  // row 4: V-irrelevant
  yield* symCursor().position.y(rowY(4), 0.4, easeInOutCubic);
  yield* stIr().opacity(0.8, 0.3);
  yield* stIr().opacity(0.35, 0.3);
  // row 5: eax = x * 5 → the immediate 5 is V
  yield* symCursor().position.y(rowY(5), 0.4, easeInOutCubic);
  yield* st2().opacity(1, 0.35);
  yield* setCaption('The immediate 5 in the binary is a compiled form of V');
  yield* st2().text('eax = x * V', 0.45);
  // row 6: eax = x * V * 2
  yield* symCursor().position.y(rowY(6), 0.4, easeInOutCubic);
  yield* st3().opacity(1, 0.35);
  yield* waitFor(0.5);

  // combine the per-instruction states into one expression
  yield* setCaption('Combining the instructions yields the symbolic state expression');
  yield* all(
    ...[st1(), st2(), st3()].map(s => all(s.position([-430, 258], 0.55, easeInOutCubic), s.opacity(0, 0.55))),
    stIr().opacity(0, 0.4),
    symHead().opacity(0, 0.4),
    symCursor().opacity(0, 0.4),
    symCard().opacity(1, 0.6),
  );
  yield* waitFor(1);

  // ============================================================
  // Phase 3 — the expression pins down the critical span (CS)
  // ============================================================
  yield* sequence(0.15, ...csRects.map(r => r.opacity(1, 0.3)));
  yield* all(csBand().opacity(1, 0.5), csBracket().end(1, 0.6), csLabel().opacity(1, 0.5));
  yield* all(seedLabel().opacity(0, 0.3), seedMark().opacity(0, 0.3));
  yield* setCaption('These instructions form the critical span (CS) — scope for the value update');
  yield* waitFor(1);

  // ============================================================
  // Phase 4 — a second scope: the safe span (SS), in another color
  // ============================================================
  yield* all(ssBracket().end(1, 0.7), ssBand().opacity(0.55, 0.6), ssLabel().opacity(1, 0.5));
  yield* setCaption('A larger scope, the safe span (SS): where enabling the update is side-effect free');
  yield* waitFor(1.2);

  // ============================================================
  // Phase 5 — x_set(V′) arrives: synthesize and attach the indirection, OFF
  // ============================================================
  yield* all(reqGrp().opacity(1, 0.35), reqGrp().scale(1, 0.45, easeOutBack));
  yield* setCaption('x_set(V′ = 10): synthesize the update from the expression');
  yield* all(indGrp().opacity(1, 0.5), indGrp().x(0, 0.5));
  // "paste" the expression into the indirection and reverse it
  exprClone().opacity(1);
  yield* exprClone().position([IND_X, 25], 0.6, easeInOutCubic);
  yield* exprClone().text('eax = (eax / (V*2)) * V′ * 2', 0.6);
  yield* all(seg1().opacity(1, 0.3), seg2().opacity(1, 0.3), seg3().opacity(1, 0.3));
  exprClone().opacity(0);
  yield* all(labRev().opacity(1, 0.35), labApp().opacity(1, 0.35));
  yield* all(trigDot().scale(1, 0.35, easeOutBack), pulseRing());
  yield* setCaption('Attach it at the CS edge — reverse the old V, apply the new V′ — still OFF');
  yield* waitFor(1.4);

  // ============================================================
  // Phase 6 — PC runs; indirection is OFF; enable only after exiting the SS
  // ============================================================
  // The PC is currently mid-SS (just before the CS).
  pc().position.y(rowY(2));
  bar().position.y(rowY(2));
  yield* all(pc().opacity(1, 0.4), pcLabel().opacity(1, 0.4), bar().opacity(1, 0.4), eaxGrp().opacity(1, 0.4));
  yield* setCaption('The PC is inside the SS — the indirection must stay OFF');
  for (let i = 3; i <= 6; i++) {
    yield* runRow(i, 0.4);
  }
  yield* setCaption('OFF: the CS executes exactly as before — eax = 30 (old V)');
  yield* runRow(7, 0.45);
  // PC leaves the SS (function returns)
  yield* all(
    pc().position.y(boxBottom + 46, 0.45, easeInOutCubic),
    bar().opacity(0, 0.3),
  );
  yield* all(pc().opacity(0, 0.3), pcLabel().opacity(0, 0.3));
  // flash the SS exit boundary, then switch the indirection ON
  ssExitLine().opacity(1);
  yield* all(flash(ssExitLine(), 3), ssExitTag().opacity(1, 0.3));
  toggleTxt().text('ON');
  yield* all(
    toggleBg().fill(GREEN, 0.3),
    toggleBg().scale(1.25, 0.25).to(1, 0.25),
    toggleTxt().scale(1.25, 0.25).to(1, 0.25),
  );
  yield* flash(toggleBg(), 2);
  yield* setCaption('The PC exited the SS — no side effects — switch the indirection ON');
  yield* all(ssExitLine().opacity(0, 0.4), ssExitTag().opacity(0, 0.4));
  yield* waitFor(0.8);

  // ============================================================
  // Phase 7 — next entry: the PC passes the indirection and it takes effect
  // ============================================================
  pc().position.y(rowY(0));
  bar().position.y(rowY(0));
  eaxVal('—');
  yield* setCaption('Next time execution enters this code…');
  yield* all(pc().opacity(1, 0.25), bar().opacity(1, 0.25));
  for (let i = 1; i <= 6; i++) {
    yield* runRow(i, 0.32);
  }
  yield* pulseRing();
  yield* setCaption('…the PC hits the indirection at the CS edge — it is ON now');
  yield* transArrow().end(1, 0.4);
  dot().opacity(1);
  yield* dot().position([593, 25], 0.55, easeInOutCubic);
  yield* all(setEax('3'), labRev().scale(1.2, 0.2).to(1, 0.2));
  yield* dot().position([791, 25], 0.4, easeInOutCubic);
  yield* all(setEax('60'), labApp().scale(1.2, 0.2).to(1, 0.2));
  yield* setCaption('eax: 30 → ÷(V*2) → 3 → ×(V′*2) → 60');
  yield* waitFor(0.8);
  dot().position([IND_X - IND_W / 2 + 30, IND_Y + IND_H / 2 + 8]);
  yield* all(retArrow().end(1, 0.5), dot().position([boxRight + 16, rowY(7) + 6], 0.5, easeInOutCubic));
  yield* dot().opacity(0, 0.25);
  yield* runRow(7, 0.4);
  yield* setCaption('Execution continues — as if V′ = 10 had been compiled in');
  yield* all(check().opacity(1, 0.4), check().scale(1.3, 0.3).to(1, 0.3), vNew().opacity(1, 0.4));
  yield* waitFor(2);

  // ============================================================
  // Phase 8 — the tuning policy plane (finale)
  // ============================================================
  yield* all(mainGrp().opacity(0.06, 0.7), policyGrp().opacity(1, 0.7), policyGrp().scale(1, 0.7));
  yield* setCaption('Different values per PID / per device — everything else stays unchanged');
  yield* waitFor(3);
});
