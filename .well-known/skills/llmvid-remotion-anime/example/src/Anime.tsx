import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import './fonts';
import {CHAT, FPS, LEAD, ME, NAME, RESULT, ROOM, S, SFX, STAMP, SUBS, beat, clockMinutes, fr} from './script';

// 리모션 애니판: 그림 파일 없이 SVG·CSS 코드로만 그린다. 1080×1920.
// 대사·시각·자막은 대본(script.json)에서 읽는다(script.ts). 이 파일에는 그리는 방법과 컷 구성만 있다.
// 새 대본으로 바꿀 때: script.json 을 새로 쓰고, 구간 구성이 달라지면 아래 '[풀이]' 의 컷을 고친다.
const INK = '#1c1726';
const OL = {stroke: INK, strokeWidth: 9, strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const};

// ───────── 소리(없어도 렌더된다) ─────────
// 음성: 기본은 null(무음). 파일을 public/audio/ 에 두고 'audio/narration.wav' 로 바꾼다.
const NARRATION: string | null = null;
// 효과음(메시지 전송음): 기본은 null. 만드는 법은 SKILL.md '효과음' 절. 예: 'audio/send.wav'. 넣는 때는 대본의 sfx.send
const SFX_SEND: string | null = null;

type Expr = 'smile' | 'flat' | 'worry' | 'shock' | 'talk' | 'angry';

const Eye: React.FC<{x: number; expr: Expr; blink: boolean; f: number}> = ({x, expr, blink, f}) => {
  const y = 482;
  if (expr === 'smile') return <path d={`M${x - 42} ${y + 8} Q${x} ${y - 46} ${x + 42} ${y + 8}`} fill="none" {...OL} strokeWidth={13} />;
  if (blink) return <path d={`M${x - 40} ${y} Q${x} ${y + 16} ${x + 40} ${y}`} fill="none" {...OL} strokeWidth={12} />;
  const pupil = expr === 'shock' ? 12 : 30;
  const lid = expr === 'worry' || expr === 'flat' ? 16 : 0;
  const look = Math.sin(f / 13) * 3;
  return (
    <g>
      <ellipse cx={x} cy={y} rx={43} ry={expr === 'shock' ? 60 : 53} fill="#fff" {...OL} strokeWidth={7} />
      <ellipse cx={x + look} cy={y + 4} rx={pupil} ry={pupil * 1.25} fill="#3b2a56" />
      <ellipse cx={x + look} cy={y + 18} rx={pupil * 0.6} ry={pupil * 0.55} fill="#7f64b5" />
      <circle cx={x + look - pupil * 0.35} cy={y - pupil * 0.45} r={Math.max(5, pupil * 0.33)} fill="#fff" />
      {lid > 0 ? <path d={`M${x - 46} ${y - 56} L${x + 46} ${y - 56} L${x + 46} ${y - 56 + lid * 2} Q${x} ${y - 52 + lid * 2.6} ${x - 46} ${y - 56 + lid * 2}Z`} fill="#f3c7a8" /> : null}
      <path d={`M${x - 48} ${y - 40 + lid * 1.8} Q${x} ${y - 72 + lid * 2} ${x + 48} ${y - 40 + lid * 1.8}`} fill="none" {...OL} strokeWidth={15} />
    </g>
  );
};

const Mouth: React.FC<{expr: Expr; talk: boolean; f: number; cx: number; cy: number}> = ({expr, talk, f, cx, cy}) => {
  const open = talk && Math.floor(f / 3) % 2 === 0;
  if (expr === 'shock') return <ellipse cx={cx} cy={cy + 8} rx={30} ry={42} fill="#7a2636" {...OL} strokeWidth={8} />;
  if (open) return <path d={`M${cx - 30} ${cy - 6} Q${cx} ${cy - 16} ${cx + 30} ${cy - 6} Q${cx + 22} ${cy + 36} ${cx} ${cy + 36} Q${cx - 22} ${cy + 36} ${cx - 30} ${cy - 6}Z`} fill="#7a2636" {...OL} strokeWidth={7} />;
  if (expr === 'smile') return <path d={`M${cx - 42} ${cy - 6} Q${cx} ${cy + 36} ${cx + 42} ${cy - 6}`} fill="none" {...OL} strokeWidth={10} />;
  if (expr === 'worry') return <path d={`M${cx - 30} ${cy + 8} Q${cx - 14} ${cy - 10} ${cx} ${cy + 6} Q${cx + 14} ${cy + 20} ${cx + 30} ${cy}`} fill="none" {...OL} strokeWidth={9} />;
  return <path d={`M${cx - 26} ${cy + 4} L${cx + 26} ${cy + 4}`} fill="none" {...OL} strokeWidth={10} />;
};

const Heroine: React.FC<{expr: Expr; talk?: boolean; blush?: boolean; phone?: boolean; dark?: boolean}> = ({expr, talk = false, blush = false, phone = false, dark = false}) => {
  const f = useCurrentFrame();
  const blink = (f + 13) % 83 < 3;
  const breathe = Math.sin(f / 16) * 5;
  return (
    <svg viewBox="0 0 800 1000" style={{width: '100%', height: '100%', overflow: 'visible', filter: dark ? 'brightness(.62) saturate(.7)' : undefined}}>
      <g transform={`translate(0 ${breathe})`}>
        <path d="M185 470 C160 170 640 170 615 470 C628 650 610 770 565 815 L235 815 C190 770 172 650 185 470Z" fill="#3b2a56" {...OL} />
        <path d="M120 1700 C130 830 270 770 400 770 C530 770 670 830 680 1700Z" fill="#5f7fd6" {...OL} />
        <path d="M120 1700 C130 900 190 845 250 815 L290 1700Z" fill="#4765b8" />
        <path d="M335 780 L400 880 L465 780 Q400 815 335 780Z" fill="#fff" {...OL} strokeWidth={7} />
        <path d="M350 680 L350 785 Q400 830 450 785 L450 680Z" fill="#e9ae8a" {...OL} strokeWidth={7} />
        <path d="M222 435 C222 265 578 265 578 435 C578 600 490 712 400 712 C310 712 222 600 222 435Z" fill="#ffdcc2" {...OL} />
        <path d="M250 560 C290 680 350 708 400 708 C330 700 290 640 250 560Z" fill="#f3c7a8" />
        {blush || expr === 'smile' ? (<g fill="#f58a8a" opacity={0.75}><ellipse cx={275} cy={570} rx={40} ry={18} /><ellipse cx={525} cy={570} rx={40} ry={18} /></g>) : null}
        <Eye x={315} expr={expr} blink={blink} f={f} />
        <Eye x={485} expr={expr} blink={blink} f={f} />
        {expr === 'worry' || expr === 'shock' ? (<g><path d="M262 408 L352 382" {...OL} strokeWidth={12} fill="none" /><path d="M538 408 L448 382" {...OL} strokeWidth={12} fill="none" /></g>) : (<g><path d="M268 398 Q312 372 356 392" {...OL} strokeWidth={10} fill="none" /><path d="M532 398 Q488 372 444 392" {...OL} strokeWidth={10} fill="none" /></g>)}
        <path d="M392 540 Q400 552 408 540" {...OL} strokeWidth={6} fill="none" />
        <Mouth expr={expr} talk={talk} f={f} cx={400} cy={612} />
        <path d="M210 440 C190 215 610 190 590 440 C565 372 525 332 470 318 C462 368 420 396 362 402 C382 366 378 342 372 322 C302 346 248 372 210 440Z" fill="#4c3669" {...OL} />
        <path d="M300 268 C350 240 450 238 505 270" fill="none" stroke="#8d72bf" strokeWidth={12} strokeLinecap="round" />
        {expr === 'worry' ? <path d={`M628 ${360 + ((f * 3) % 60)} q22 44 0 58 q-22 -14 0 -58Z`} fill="#8fd6f5" {...OL} strokeWidth={6} /> : null}
        {phone ? (<g><rect x={318} y={770} width={170} height={236} rx={26} fill="#262335" {...OL} /><circle cx={348} cy={806} r={14} fill="#5a5570" /><ellipse cx={304} cy={900} rx={40} ry={54} fill="#ffdcc2" {...OL} /><ellipse cx={502} cy={900} rx={40} ry={54} fill="#ffdcc2" {...OL} /></g>) : null}
      </g>
    </svg>
  );
};

const Boss: React.FC<{expr: Expr; talk?: boolean}> = ({expr, talk = false}) => {
  const f = useCurrentFrame();
  const glint = ((f % 70) / 70) * 130;
  return (
    <svg viewBox="0 0 800 1000" style={{width: '100%', height: '100%', overflow: 'visible'}}>
      <g transform={`translate(0 ${Math.sin(f / 19) * 4})`}>
        <path d="M90 1700 C110 830 270 780 400 780 C530 780 690 830 710 1700Z" fill="#2c3560" {...OL} />
        <path d="M330 790 L400 900 L470 790Z" fill="#fff" {...OL} strokeWidth={7} />
        <path d="M375 845 L425 845 L445 1700 L355 1700Z" fill="#b63a4e" {...OL} strokeWidth={7} />
        <path d="M340 690 L340 795 Q400 835 460 795 L460 690Z" fill="#d9a07e" {...OL} strokeWidth={7} />
        <path d="M212 400 C212 250 588 250 588 400 L588 520 C588 650 500 725 400 725 C300 725 212 650 212 520Z" fill="#f2c8a5" {...OL} />
        <path d="M200 420 C180 210 620 190 600 410 L570 350 C480 350 390 335 330 290 C310 335 260 355 230 355Z" fill="#6d7283" {...OL} />
        <g>
          <rect x={250} y={438} width={130} height={92} rx={16} fill="#fdfbf4" {...OL} />
          <rect x={420} y={438} width={130} height={92} rx={16} fill="#fdfbf4" {...OL} />
          <path d="M380 470 L420 470" {...OL} fill="none" />
          <circle cx={315} cy={486} r={15} fill={INK} /><circle cx={485} cy={486} r={15} fill={INK} />
          <rect x={258 + glint * 0.8} y={446} width={13} height={76} fill="#cfe6f5" opacity={glint < 130 ? 0.85 : 0} />
        </g>
        <path d={expr === 'angry' ? 'M242 398 L372 430' : 'M242 410 Q306 390 372 412'} {...OL} strokeWidth={22} fill="none" />
        <path d={expr === 'angry' ? 'M558 398 L428 430' : 'M558 410 Q494 390 428 412'} {...OL} strokeWidth={22} fill="none" />
        <Mouth expr={expr} talk={talk} f={f} cx={400} cy={625} />
      </g>
    </svg>
  );
};

const OfficeBg: React.FC<{dark?: boolean}> = ({dark = false}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: dark ? 'linear-gradient(#17152e,#2b2448 62%,#3b2c52)' : 'linear-gradient(#ffeccc,#f7d9b0 58%,#d99a6a 60%,#b77b52)'}}>
      <div style={{position: 'absolute', left: 90, top: 150, width: 460, height: 620, borderRadius: 18, background: dark ? 'linear-gradient(#0d1538,#1e2c63)' : 'linear-gradient(#a8ddf6,#e7f6ff 70%,#fff3d1)', border: `10px solid ${INK}`, overflow: 'hidden'}}>
        {[60, 170, 280, 380].map((x, i) => <div key={x} style={{position: 'absolute', left: x, bottom: 0, width: 80, height: 170 + (i * 97) % 260, background: dark ? '#33406f' : '#c0d6e6', filter: 'blur(3px)'}} />)}
        <div style={{position: 'absolute', left: 226, top: 0, width: 10, height: '100%', background: INK}} />
        <div style={{position: 'absolute', left: 0, top: 300, width: '100%', height: 10, background: INK}} />
      </div>
      <div style={{position: 'absolute', right: 70, top: 380, width: 360, height: 250, borderRadius: 16, background: '#2b2b3e', border: `10px solid ${INK}`}}><div style={{margin: 16, height: 196, borderRadius: 6, background: `linear-gradient(120deg,#6dd0d6,#3f8fbf ${50 + Math.sin(f / 20) * 10}%,#2a5f96)`}} /></div>
      <div style={{position: 'absolute', right: 225, top: 640, width: 50, height: 70, background: '#2b2b3e', border: `8px solid ${INK}`}} />
      {!dark ? <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1300, background: 'linear-gradient(115deg,rgba(255,255,255,.42),transparent 42%)'}} /> : null}
    </AbsoluteFill>
  );
};

const FocusLines: React.FC<{color?: string; opacity?: number}> = ({color = '#fff', opacity = 0.9}) => {
  const f = useCurrentFrame();
  const seed = Math.floor(f / 3);
  const lines = Array.from({length: 46}, (_, i) => {
    const a = (i / 46) * Math.PI * 2 + (((i * 73 + seed * 31) % 17) / 17) * 0.1;
    const inner = 620 + ((i * 41 + seed * 7) % 180);
    const w = 0.012 + ((i * 7) % 4) * 0.004;
    const R = 1500;
    const p = (r: number, t: number) => `${540 + Math.cos(t) * r},${820 + Math.sin(t) * r}`;
    return `M${p(R, a - w)} L${p(inner, a)} L${p(R, a + w)}Z`;
  });
  return <svg viewBox="0 0 1080 1920" style={{position: 'absolute', inset: 0, opacity}}><path d={lines.join(' ')} fill={color} /></svg>;
};

// ───────── 단톡 화면: 대본의 대화를 시각대로 보여 준다 ─────────
// offset = 이 컷이 시작하는 프레임(영상 전체 기준). 내 메시지는 보내기 34프레임 전부터 입력창에 한 글자씩 쳐진다.
const ChatScreen: React.FC<{offset: number}> = ({offset}) => {
  const f = useCurrentFrame();
  const {fps: F} = useVideoConfig();
  const g = f + offset;
  const shown = CHAT.filter((m) => g >= fr(m.t)).slice(-5);
  const next = CHAT.find((m) => m.who === ME && fr(m.t) > g);
  const n = next ? Math.floor(interpolate(g, [fr(next.t) - 34, fr(next.t) - 6], [0, next.text.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})) : 0;
  const inputText = next ? next.text.slice(0, n) : '';
  return (
    <AbsoluteFill style={{background: 'linear-gradient(160deg,#2d2a55,#514079 60%,#a9627d)'}}>
      <div style={{position: 'absolute', left: 90, top: 110, width: 900, height: 1500, borderRadius: 90, background: '#17151f', border: `10px solid ${INK}`, boxShadow: '0 30px 0 rgba(0,0,0,.35)'}}>
        <div style={{position: 'absolute', inset: 26, borderRadius: 66, background: '#bcd0e2', overflow: 'hidden', fontFamily: 'KR', color: INK}}>
          <div style={{height: 150, background: '#54688a', color: '#fff', fontSize: 50, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{ROOM}</div>
          <div style={{padding: '40px 36px'}}>
            {shown.map((m) => {
              const me = m.who === ME;
              const s = spring({frame: g - fr(m.t), fps: F, config: {damping: 12, stiffness: 190}});
              return (
                <div key={m.t} style={{display: 'flex', justifyContent: me ? 'flex-end' : 'flex-start', marginBottom: 34, transform: `scale(${s})`, transformOrigin: me ? '100% 50%' : '0% 50%'}}>
                  {/* 말풍선 옆 얼굴 색: 정하는 사람(마지막 등장인물)은 주황, 나머지는 파랑 */}
                  {!me ? <div style={{width: 92, height: 92, borderRadius: 34, background: m.who === LEAD ? '#ef8f5f' : '#6ab0ef', marginRight: 18, border: `6px solid ${INK}`, flex: 'none'}} /> : null}
                  <div>
                    {!me ? <div style={{fontSize: 34, marginBottom: 8}}>{NAME[m.who] ?? m.who}</div> : null}
                    <div style={{background: me ? '#ffe36b' : '#fff', padding: '20px 30px', borderRadius: 30, fontSize: 48, border: `5px solid ${INK}`, maxWidth: 640}}>{m.text}</div>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 150, background: '#fff', borderTop: `6px solid ${INK}`, display: 'flex', alignItems: 'center', padding: '0 36px', fontSize: 46}}>
            <span>{inputText}</span>
            <span style={{width: 6, height: 58, background: INK, marginLeft: 6, opacity: Math.floor(f / 8) % 2 ? 0 : 1}} />
            <div style={{marginLeft: 'auto', width: 92, height: 92, borderRadius: 30, background: inputText ? '#ffe36b' : '#d9dee7', border: `5px solid ${INK}`}} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 자막: 대본의 subs. 한 줄 12자 이하, 두 줄까지.
const Subtitles: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const s = SUBS.find(([a, b]) => t >= a && t < b);
  if (!s) return null;
  return <div style={{position: 'absolute', left: 90, width: 900, top: 1290, textAlign: 'center', color: '#fff', fontFamily: 'KR', fontSize: 74, lineHeight: 1.25, whiteSpace: 'pre-line', WebkitTextStroke: `14px ${INK}`, paintOrder: 'stroke fill'}}>{s[2]}</div>;
};

const Figure: React.FC<{children: React.ReactNode; size?: number; x?: number; y?: number}> = ({children, size = 1080, x = 0, y = 230}) => <div style={{position: 'absolute', left: x, top: y, width: size, height: size * 1.25}}>{children}</div>;

// 구간 키워드 칩(화면 위쪽)
const Chip: React.FC<{text?: string; top?: number}> = ({text, top = 130}) => {
  const f = useCurrentFrame();
  const {fps: F} = useVideoConfig();
  if (!text) return null;
  const s = spring({frame: f, fps: F, config: {damping: 11, stiffness: 200}});
  return <div style={{position: 'absolute', left: 0, right: 0, top, display: 'flex', justifyContent: 'center'}}><div style={{background: '#fff', border: `10px solid ${INK}`, borderRadius: 60, padding: '10px 60px', fontFamily: 'Head', fontSize: 110, color: INK, transform: `scale(${s})`}}>{text}</div></div>;
};

type Cut = React.FC<{offset: number; dur: number}>;

// ───────── [풀이] 컷: 대본의 구간 하나가 컷 하나다. 문구와 시각은 대본에서 읽는다 ─────────
// 묻기: 단톡에 내 질문을 치고 보낸다 → 보낸 뒤 휴대폰을 든 주인공
const Hook: Cut = ({offset, dur}) => {
  const f = useCurrentFrame();
  const sent = CHAT.find((m) => m.who === ME);
  const cut = sent ? fr(sent.t) - offset + 8 : dur;
  if (f < cut) return <ChatScreen offset={offset} />;
  return <AbsoluteFill><OfficeBg /><Figure><Heroine expr="smile" phone blush talk /></Figure><Chip text={beat('hook').keyword} /></AbsoluteFill>;
};

// 대답: 답이 차례로 온다 → 마지막 답 뒤에 난감한 주인공
const Ask: Cut = ({offset, dur}) => {
  const f = useCurrentFrame();
  const b = beat('ask');
  const last = (b.chat ?? []).reduce((acc, m) => Math.max(acc, fr(m.t) - offset), 0);
  if (f < Math.min(dur - 16, last + 14)) return <ChatScreen offset={offset} />;
  return <AbsoluteFill style={{background: '#7c2f4b'}}><FocusLines opacity={0.5} /><Figure y={300}><Heroine expr="worry" phone /></Figure><Chip text={b.keyword} /></AbsoluteFill>;
};

// 기다림: 시계가 돌고 눈금이 찬다. 주인공은 지쳐 간다
const Wait: Cut = ({dur}) => {
  const f = useCurrentFrame();
  const b = beat('wait');
  const k = interpolate(f, [6, dur - 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const a0 = clockMinutes(b.clock?.from ?? '0:00');
  let a1 = clockMinutes(b.clock?.to ?? '0:00');
  if (a1 < a0) a1 += 720;
  const now = a0 + (a1 - a0) * k;
  const g = b.gauge ?? {label: '', from: 0, to: 1};
  const val = g.from + (g.to - g.from) * k;
  const hand = (turn: number, len: number) => ({x2: 300 + Math.sin(turn * Math.PI * 2) * len, y2: 300 - Math.cos(turn * Math.PI * 2) * len});
  const shake = val > 0.9 ? (f % 4 < 2 ? 4 : -4) : 0;
  return (
    <AbsoluteFill>
      <OfficeBg dark={k > 0.7} />
      <svg viewBox="0 0 600 600" style={{position: 'absolute', left: 310, top: 120, width: 460, height: 460}}>
        <circle cx={300} cy={300} r={270} fill="#fffaf0" {...OL} strokeWidth={18} />
        {Array.from({length: 12}, (_, i) => {
          const a = (i / 12) * Math.PI * 2;
          return <line key={i} x1={300 + Math.sin(a) * 222} y1={300 - Math.cos(a) * 222} x2={300 + Math.sin(a) * 250} y2={300 - Math.cos(a) * 250} {...OL} strokeWidth={i % 3 === 0 ? 16 : 9} />;
        })}
        <line x1={300} y1={300} {...hand(now / 720, 135)} {...OL} strokeWidth={24} />
        <line x1={300} y1={300} {...hand(now / 60, 205)} {...OL} strokeWidth={14} />
        <circle cx={300} cy={300} r={18} fill={INK} />
      </svg>
      <div style={{position: 'absolute', left: 150 + shake, top: 620, width: 780, fontFamily: 'KR', color: '#fff', WebkitTextStroke: `10px ${INK}`, paintOrder: 'stroke fill', fontSize: 56, display: 'flex', justifyContent: 'space-between'}}><span>{g.label}</span><span>{Math.round(val * 100)}%</span></div>
      <div style={{position: 'absolute', left: 150 + shake, top: 700, width: 780, height: 70, borderRadius: 40, background: '#fff', border: `10px solid ${INK}`, overflow: 'hidden'}}><div style={{width: `${val * 100}%`, height: '100%', background: val > 0.8 ? '#d6304c' : '#ef8f5f'}} /></div>
      <Figure size={560} x={260} y={800}><Heroine expr={k > 0.35 ? 'worry' : 'flat'} dark={k > 0.7} /></Figure>
    </AbsoluteFill>
  );
};

// 결정: 놀란 주인공 위로 알림이 떨어진다 → 정하는 사람의 얼굴이 크게 나온다
const Decide: Cut = ({offset, dur}) => {
  const f = useCurrentFrame();
  const {fps: F} = useVideoConfig();
  const b = beat('decide');
  const m = (b.chat ?? [])[0];
  const at = m ? fr(m.t) - offset : 0;
  const half = at + 34;
  if (!m || f < half) {
    const s = spring({frame: f - at, fps: F, config: {damping: 11, stiffness: 180}});
    const sh = f >= at && f < at + 30 ? (f % 4 < 2 ? 5 : -5) : 0;
    return (
      <AbsoluteFill style={{background: '#7c2f4b'}}><FocusLines />
        <Figure y={300}><Heroine expr={m && f >= at ? 'shock' : 'worry'} phone /></Figure>
        {m && f >= at ? (
          <div style={{position: 'absolute', left: 90 + sh, top: 110 - (1 - s) * 400, width: 900, height: 270, background: '#fff', borderRadius: 42, border: `10px solid ${INK}`, display: 'flex', alignItems: 'center', fontFamily: 'KR', padding: 30}}>
            <div style={{width: 150, height: 150, borderRadius: 50, background: '#ef8f5f', border: `8px solid ${INK}`, marginRight: 34, flex: 'none'}} />
            <div><div style={{fontSize: 52}}>{NAME[m.who] ?? m.who} · {ROOM}</div><div style={{fontSize: 62, color: '#b63a4e', marginTop: 10}}>{m.text}</div></div>
          </div>
        ) : null}
      </AbsoluteFill>
    );
  }
  const local = f - half;
  const hit = local < 3;
  const k = interpolate(local, [3, 12], [0.92, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.back(2))});
  return (
    <AbsoluteFill style={{background: hit ? '#fff' : '#2a1838'}}><FocusLines color={hit ? '#1c1726' : '#b63a4e'} />
      <div style={{position: 'absolute', left: -180, top: -60, width: 1440, height: 1800, transform: `scale(${hit ? 1.0 : k})`, transformOrigin: '50% 40%'}}><Boss expr="flat" talk={local > 4 && f < dur - 6} /></div>
    </AbsoluteFill>
  );
};

// 결말: 결과가 적힌 종이에 도장이 찍힌다. 이 구간의 대답은 종이 아래에 한 줄씩 뜬다
const Punch: Cut = ({offset}) => {
  const f = useCurrentFrame();
  const impact = STAMP ? fr(STAMP.t) - offset : 99999;
  const down = interpolate(f, [impact - 26, impact], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic)});
  const hit = f >= impact && f < impact + 3;
  const replies = (beat('punch').chat ?? []).filter((m) => f + offset >= fr(m.t));
  return (
    <AbsoluteFill style={{background: hit ? '#fff' : '#2e7b82'}}>
      <div style={{position: 'absolute', left: 150, top: 130, width: 780, height: 1060, background: '#fbf7ea', border: `12px solid ${INK}`, borderRadius: 26, fontFamily: 'KR', textAlign: 'center'}}>
        <div style={{fontFamily: 'Head', fontSize: 84, marginTop: 56}}>{S.title}</div>
        <div style={{height: 8, background: INK, margin: '30px 70px'}} />
        <div style={{fontFamily: 'Head', fontSize: 92, color: '#b63a4e'}}>{RESULT}</div>
        <svg viewBox="0 0 400 300" width={520} height={390} style={{marginTop: 10}}>
          {[130, 200, 270].map((x, i) => <path key={x} d={`M${x} ${96 - ((f * 2 + i * 9) % 26)} q14 -22 0 -44 q-14 -22 0 -44`} fill="none" stroke="#9aa3ad" strokeWidth={10} strokeLinecap="round" opacity={0.8} />)}
          <rect x={22} y={150} width={56} height={30} rx={12} fill={INK} /><rect x={322} y={150} width={56} height={30} rx={12} fill={INK} />
          <path d="M70 140 L330 140 L310 268 Q200 292 90 268Z" fill="#2b2b3e" {...OL} />
          <ellipse cx={200} cy={140} rx={130} ry={30} fill="#d6402c" {...OL} />
          {[[150, 136, '#fdfbf4'], [205, 146, '#fdfbf4'], [250, 132, '#5faa50'], [178, 150, '#5faa50'], [228, 128, '#f0a050']].map(([x, y, c], i) => <rect key={i} x={Number(x) - 16} y={Number(y) - 9} width={32} height={18} rx={4} fill={String(c)} />)}
        </svg>
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 44, fontSize: 46, lineHeight: 1.3}}>{replies.map((m) => <div key={m.t}>{NAME[m.who] ?? m.who}: {m.text}</div>)}</div>
      </div>
      {STAMP && f >= impact ? <div style={{position: 'absolute', left: 330, top: 858, width: 420, height: 170, border: '16px solid #d33a4c', borderRadius: 26, color: '#d33a4c', fontFamily: 'Head', fontSize: 108, textAlign: 'center', lineHeight: '136px', whiteSpace: 'nowrap', transform: 'rotate(-9deg)'}}>{STAMP.text}</div> : null}
      {STAMP && f < impact + 6 ? <div style={{position: 'absolute', left: 365, top: -560 + down * 1040, width: 340, height: 500}}><div style={{width: 110, height: 330, margin: '0 auto', background: '#5b3a2e', border: `10px solid ${INK}`}} /><div style={{width: 340, height: 150, background: '#c98c55', border: `10px solid ${INK}`, borderRadius: 16}} /></div> : null}
      {f > impact && f < impact + 14 ? <FocusLines color="#ffd65c" opacity={1 - (f - impact) / 14} /> : null}
    </AbsoluteFill>
  );
};

// [풀이] 구간 id → 컷. 대본의 구간 id 가 달라지면 여기와 위 컷을 고친다(없는 id 의 구간은 검은 화면이 된다)
const CUTS: Record<string, Cut> = {hook: Hook, ask: Ask, wait: Wait, decide: Decide, punch: Punch};

export const Anime: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    {S.beats.map((b) => {
      const C = CUTS[b.id];
      const from = fr(b.start);
      const d = fr(b.end) - from;
      return C ? <Sequence key={b.id} from={from} durationInFrames={d} premountFor={0}><C offset={from} dur={d} /></Sequence> : null;
    })}
    <Subtitles />
    {NARRATION ? <Audio src={staticFile(NARRATION)} volume={1} /> : null}
    {SFX_SEND ? SFX.send.map((at) => <Sequence key={at} from={at}><Audio src={staticFile(SFX_SEND)} volume={0.7} /></Sequence>) : null}
  </AbsoluteFill>
);
