import React from 'react';
import {useCurrentFrame} from 'remotion';
import {getSceneIndexForFrame, STORY_SCENES} from './StoryData';
import {PaperRoom, PaperPerson, PaperDesk} from './PaperAssets';
import {LEAD, ME, RESULT, S, STAMP, beat, clockMinutes, fr} from './script';

// 관절 종이인형 장면. 장면 하나가 대본(script.json)의 구간 하나다. 문구와 시각은 대본에서 읽는다.
// [풀이] 구간 id(hook, ask, wait, decide, punch)마다 무엇을 보여 줄지가 아래 블록에 있다. 구간 구성이 다른 대본이면 블록을 고친다.
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const ease = (x: number) => {
  const t = clamp(x);
  return t * t * (3 - 2 * t);
};
const FONT = 'MotionCaption, sans-serif';
const INK = '#2b2a33';
// 등장인물 순서 → 인형 종류(첫째 주인공, 둘째 동료, 마지막 정하는 사람)
const KIND: ('woman' | 'new' | 'lead')[] = ['woman', 'new', 'lead'];
const kindOf = (who: string) => KIND[Math.min(KIND.length - 1, Math.max(0, S.cast.findIndex((c) => c.id === who)))];

const Chair: React.FC<{x: number; y: number; s?: number}> = ({x, y, s = 1}) => <g transform={`translate(${x} ${y}) scale(${s})`} filter="url(#card)"><path d="M9 0Q110 -18 155 3L153 162L13 164Z" fill="#6a8989" stroke="#4a6b6c" strokeWidth="4" /><path d="M-2 161L174 151L175 176L0 186Z" fill="#486872" /><path d="M78 179L95 178L96 288L75 291Z" fill="#3a5862" /><path d="M19 289L152 280" stroke="#3a5862" strokeWidth="13" /><circle cx="22" cy="297" r="11" fill="#324854" /><circle cx="151" cy="289" r="11" fill="#324854" /></g>;

// 오려 붙인 말풍선. show = 나타난 뒤 지난 프레임(음수면 아직 안 보인다). side: 꼬리가 왼쪽(1)·오른쪽(-1)
const Bubble: React.FC<{x: number; y: number; text: string; show: number; side?: 1 | -1; color?: string}> = ({x, y, text, show, side = 1, color = '#fffdf4'}) => {
  if (show < 0) return null;
  const k = 0.55 + 0.45 * ease(show / 5) + (show < 8 ? Math.sin((show / 8) * Math.PI) * 0.08 : 0);
  const w = Math.max(230, text.length * 60 + 90);
  const tail = side > 0 ? `H96L54 172L60 122H0Z` : `H${w - 60}L${w - 54} 172L${w - 96} 122H0Z`; // 아래쪽 꼬리
  return <g transform={`translate(${x} ${y}) rotate(${-3 * side}) scale(${k})`} filter="url(#card)"><path d={`M0 0H${w}V122${tail}`} fill={color} stroke="#cdbf9c" strokeWidth="3" /><text x={w / 2} y={82} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={58} fill={INK}>{text}</text></g>;
};

// 종이 시계. minutes = 12시간 기준 분
const Clock: React.FC<{x: number; y: number; r: number; minutes: number}> = ({x, y, r, minutes}) => {
  const hand = (turn: number, len: number, wd: number) => <path d={`M0 0L${Math.sin(turn * Math.PI * 2) * len} ${-Math.cos(turn * Math.PI * 2) * len}`} stroke={INK} strokeWidth={wd} strokeLinecap="round" />;
  return <g transform={`translate(${x} ${y})`} filter="url(#card)"><circle r={r + 16} fill="#c9573f" /><circle r={r} fill="#fffaf0" />{Array.from({length: 12}, (_, i) => <path key={i} d={`M${Math.sin((i / 12) * Math.PI * 2) * r * 0.8} ${-Math.cos((i / 12) * Math.PI * 2) * r * 0.8}L${Math.sin((i / 12) * Math.PI * 2) * r * 0.92} ${-Math.cos((i / 12) * Math.PI * 2) * r * 0.92}`} stroke="#8d8a80" strokeWidth={i % 3 === 0 ? 10 : 5} strokeLinecap="round" />)}{hand(minutes / 720, r * 0.5, 16)}{hand(minutes / 60, r * 0.78, 9)}<circle r={11} fill={INK} /></g>;
};

// 종이 눈금 띠. val 0~1
const Gauge: React.FC<{x: number; y: number; w: number; val: number; label: string}> = ({x, y, w, val, label}) => <g transform={`translate(${x} ${y}) rotate(-2)`} filter="url(#card)"><path d={`M0 0H${w}V150H0Z`} fill="#fffdf4" stroke="#cdbf9c" strokeWidth="3" /><text x={28} y={58} fontFamily={FONT} fontWeight={700} fontSize={46} fill={INK}>{label}</text><text x={w - 28} y={58} textAnchor="end" fontFamily={FONT} fontWeight={700} fontSize={46} fill={INK}>{Math.round(val * 100)}%</text><path d={`M28 84H${w - 28}V124H28Z`} fill="#e5dcc3" /><path d={`M28 84H${28 + (w - 56) * val}V124H28Z`} fill={val > 0.8 ? '#c9573f' : '#e39a52'} /></g>;

// 결과가 적힌 종이 간판 + 김 나는 냄비. stamp = 도장이 찍힌 뒤 지난 프레임(음수면 아직)
const Sign: React.FC<{x: number; y: number; tick: number; stamp: number}> = ({x, y, tick, stamp}) => {
  const k = stamp >= 0 ? 1 + Math.max(0, 1 - stamp / 4) * 1.4 : 0;
  return <g transform={`translate(${x} ${y}) rotate(1.5)`} filter="url(#card)">
    <path d="M0 0H600V700H0Z" fill="#fffdf4" stroke="#cdbf9c" strokeWidth="4" />
    <text x={300} y={92} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={54} fill={INK}>{S.title}</text>
    <path d="M50 124H550" stroke={INK} strokeWidth="6" />
    <text x={300} y={236} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={104} fill="#b8442e">{RESULT}</text>
    {[220, 300, 380].map((sx, i) => <path key={sx} d={`M${sx} ${340 - ((tick + i * 2) % 5) * 6}q16 -24 0 -46`} fill="none" stroke="#b9b3a5" strokeWidth="10" strokeLinecap="round" />)}
    <path d="M118 396H482L458 560Q300 596 142 560Z" fill="#3c3a45" /><path d="M70 404H130V440H70ZM470 404H530V440H470Z" fill="#3c3a45" /><ellipse cx={300} cy={396} rx={182} ry={34} fill="#c9462e" />
    {[[230, 390, '#fff6e0'], [300, 402, '#fff6e0'], [356, 386, '#6a9c5a'], [266, 404, '#6a9c5a'], [330, 380, '#e39a52']].map(([px, py, c], i) => <path key={i} d={`M${Number(px) - 20} ${Number(py) - 10}h40v20h-40z`} fill={String(c)} />)}
    {STAMP && stamp >= 0 ? <g transform={`translate(430 620) rotate(-9) scale(${k})`}><path d="M-150 -62H150V62H-150Z" fill="none" stroke="#c9302c" strokeWidth="14" /><text y={30} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={88} fill="#c9302c">{STAMP.text}</text></g> : null}
  </g>;
};

export const PaperScene: React.FC<{preview?: boolean}> = ({preview = false}) => {
  const frame = useCurrentFrame(), tick = Math.floor(frame / 2);
  const last = STORY_SCENES.length - 1;
  const i = preview ? [0, Math.min(2, last), last][Math.floor((frame % 144) / 48)] : getSceneIndexForFrame(frame);
  const sc = STORY_SCENES[i], len = sc.endFrame - sc.startFrame;
  const p = preview ? (frame % 48) / 47 : clamp((frame - sc.startFrame) / len);
  const lf = Math.round(p * len); // 장면 안에서 지난 프레임
  const since = (sec: number) => lf - (fr(sec) - sc.startFrame); // 대본의 그 초부터 지난 프레임(음수면 아직)
  const id = sc.id;
  const wait = beat('wait');
  const m0 = clockMinutes(wait.clock?.from ?? '0:00');
  let m1 = clockMinutes(wait.clock?.to ?? '0:00');
  if (m1 < m0) m1 += 720;
  const g = wait.gauge ?? {label: '', from: 0, to: 1};
  const kWait = ease((p - 0.05) / 0.85);
  const leadX = 900 - ease(p / 0.45) * 420;
  return <svg width="1080" height="1920" viewBox="0 0 1080 1920" style={{display: 'block', background: '#efe6cb'}}>
    <PaperRoom />
    {id === 'hook' && <>
      {/* 묻기: 주인공이 자리에서 묻는다 */}
      <Chair x={110} y={960} s={1.35} />
      <PaperPerson x={56} y={452} s={1.6} pose="seat" tick={tick} look={1} brow={p > 0.7} typing />
      <PaperDesk x={22} y={1110} s={1.08} />
      <path d={`M403 ${1070 + (tick % 2) * 4}q-14 -17 -28 -7l-8 23 38 6z`} fill="#efc19c" stroke="#c89777" strokeWidth="2" />
      {(beat('hook').chat ?? []).map((c) => <Bubble key={c.t} x={330} y={250} text={c.text} show={since(c.t)} color="#ffe9a8" />)}
    </>}
    {id === 'ask' && <>
      {/* 대답: 두 사람이 차례로 답한다. 말풍선은 대본의 대화 시각에 뜬다 */}
      <Chair x={135} y={1013} /><Chair x={720} y={1013} />
      <PaperPerson x={372} y={600} s={1.0} kind="lead" pose="stand" tick={tick + 5} look={-1} />
      <PaperPerson x={50} y={470} s={1.4} pose="seat" tick={tick} look={1} brow={p > 0.5} />
      <PaperPerson x={618} y={470} s={1.4} pose="seat" tick={tick + 11} kind="new" look={-1} />
      <PaperDesk x={-192} y={1180} s={1.2} monitor={false} /><PaperDesk x={673} y={1180} s={1.2} monitor={false} />
      {(beat('ask').chat ?? []).map((c) => c.who === LEAD
        ? <Bubble key={c.t} x={300} y={380} text={c.text} show={since(c.t)} />
        : <Bubble key={c.t} x={470} y={250} text={c.text} show={since(c.t)} side={-1} />)}
    </>}
    {id === 'wait' && <>
      {/* 기다림: 시계가 돌고 눈금이 찬다. 주인공은 고개를 떨군다 */}
      <path d="M0 0H1080V1920H0Z" fill="#edb66f" opacity={0.05 + kWait * 0.16} />
      <Clock x={820} y={380} r={170} minutes={m0 + (m1 - m0) * kWait} />
      <Gauge x={70} y={150} w={560} val={g.from + (g.to - g.from) * kWait} label={g.label} />
      <PaperPerson x={90 - ease(p) * 10} y={470 + ease(p) * 26} s={2.2} pose="seat" tick={tick} look={p > 0.5 ? -1 : 0} brow />
      <PaperDesk x={-95} y={1250} s={2.6} monitor={false} />
    </>}
    {id === 'decide' && <>
      {/* 결정: 정하는 사람이 걸어 들어와 한마디 한다 */}
      <Chair x={80} y={1010} s={0.9} /><PaperDesk x={-310} y={1133} s={1} />
      <PaperPerson x={18} y={640} s={1.05} pose="seat" tick={tick} look={1} brow={p > 0.3} />
      <PaperPerson x={leadX} y={610} s={1.2} kind={kindOf(LEAD)} pose={p < 0.45 ? 'walk' : 'stand'} tick={tick} look={-1} />
      {(beat('decide').chat ?? []).map((c) => <Bubble key={c.t} x={Math.max(60, Math.min(520, leadX - 180))} y={330} text={c.text} show={since(c.t) - 6} side={-1} color="#ffd9c9" />)}
    </>}
    {id === 'punch' && <>
      {/* 결말: 결과 간판이 내려오고 도장이 찍힌다. 두 사람이 답한다 */}
      <Sign x={240} y={220 - (1 - ease(p / 0.12)) * 1000} tick={tick} stamp={STAMP ? since(STAMP.t) : -1} />
      <Chair x={82} y={1218} s={0.82} /><Chair x={792} y={1218} s={0.82} />
      <PaperPerson x={10} y={770} s={1.15} pose="seat" tick={tick} look={1} />
      <PaperPerson x={716} y={770} s={1.15} pose="seat" tick={tick + 7} kind="new" look={-1} />
      {(beat('punch').chat ?? []).map((c) => c.who === ME
        ? <Bubble key={c.t} x={30} y={960} text={c.text} show={since(c.t)} color="#ffe9a8" />
        : <Bubble key={c.t} x={800} y={960} text={c.text} show={since(c.t)} side={-1} />)}
    </>}
    <path d="M-25 1742Q84 1702 157 1740L138 1920H-10Z" fill="#b48e6d" /><path d="M60 1770L82 1650M74 1702Q-6 1690 12 1621Q87 1636 74 1702M80 1672Q155 1640 154 1586Q78 1594 80 1672" fill="#739b77" stroke="#658c69" strokeWidth="6" />
    <rect width="1080" height="1920" fill="url(#fibers)" pointerEvents="none" />
  </svg>;
};
