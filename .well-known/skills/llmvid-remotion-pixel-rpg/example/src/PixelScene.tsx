import React from 'react';
import {useCurrentFrame} from 'remotion';
import {getSceneIndexForFrame, STORY_SCENES} from './StoryData';
import {PixelActor, PixelDesk, PixelRoom} from './PixelAssets';
import {CHAT, LEAD, NAME, RESULT, S, STAMP, beat, clockMinutes, fr} from './script';

// 픽셀 RPG 장면(270×480 을 네 배로 키운다). 장면 하나가 대본(script.json)의 구간 하나다. 문구와 시각은 대본에서 읽는다.
// [풀이] 구간 id(hook, ask, wait, decide, punch)마다 무엇을 보여 줄지가 아래 블록에 있다. 구간 구성이 다른 대본이면 블록을 고친다.
// 대화는 화면 위 RPG 대사창에 한 글자씩 찍힌다.
const clamp = (n: number) => Math.max(0, Math.min(1, n));
const ease = (n: number) => {
  const t = clamp(n);
  return t * t * (3 - 2 * t);
};
const FONT = 'MotionCaption, sans-serif';
// 등장인물 순서 → 도트 인물 종류(첫째 주인공, 둘째 동료, 마지막 정하는 사람)
const KIND: ('woman' | 'new' | 'lead')[] = ['woman', 'new', 'lead'];
const kindOf = (who: string) => KIND[Math.min(KIND.length - 1, Math.max(0, S.cast.findIndex((c) => c.id === who)))];

const Chair: React.FC<{x: number; y: number; s?: number}> = ({x, y, s = 1}) => <g transform={`translate(${x} ${y}) scale(${s})`}><path d="M3 0h26v38H3z" fill="#38565e" /><path d="M6 3h20v28H6z" fill="#5c7d7f" /><path d="M0 38h34v6H0zM14 44h6v19h-6zM3 62h29v3H3z" fill="#304750" /><path d="M2 65h5v3H2zM28 65h5v3h-5z" fill="#243a45" /></g>;

// RPG 대사창: 이름표 + 한 글자씩 찍히는 대사. show = 그 대사가 시작된 뒤 지난 프레임
const MsgWindow: React.FC<{who: string; text: string; show: number; tick: number}> = ({who, text, show, tick}) => {
  const n = Math.max(0, Math.min(text.length, Math.floor(show / 1.5) + 1));
  const lead = who === LEAD;
  return <g>
    <path d="M8 22h254v60H8z" fill="#141a28" /><path d="M10 24h250v56H10z" fill="#f4eed8" /><path d="M12 26h246v52H12z" fill="#263247" />
    <path d="M16 12h64v16H16z" fill="#141a28" /><path d="M18 14h60v12H18z" fill={lead ? '#d78265' : '#5c9bd6'} />
    <text x={48} y={24} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={10} fill="#141a28">{NAME[who] ?? who}</text>
    <text x={22} y={59} fontFamily={FONT} fontWeight={700} fontSize={18} fill="#fff9e2">{text.slice(0, n)}</text>
    {n >= text.length && tick % 2 === 0 ? <path d="M244 66h8v3h-2v3h-4v-3h-2z" fill="#fff9e2" /> : null}
  </g>;
};

// 도트 시계. minutes = 12시간 기준 분
const Clock: React.FC<{x: number; y: number; r: number; minutes: number}> = ({x, y, r, minutes}) => {
  const tip = (turn: number, len: number) => `M0 0L${Math.round(Math.sin(turn * Math.PI * 2) * len)} ${Math.round(-Math.cos(turn * Math.PI * 2) * len)}`;
  return <g transform={`translate(${x} ${y})`}><circle r={r + 3} fill="#243a45" /><circle r={r} fill="#fff9e2" />{[0, 3, 6, 9].map((i) => <rect key={i} x={Math.round(Math.sin((i / 12) * Math.PI * 2) * (r - 4)) - 1} y={Math.round(-Math.cos((i / 12) * Math.PI * 2) * (r - 4)) - 1} width={3} height={3} fill="#8a8f86" />)}<path d={tip(minutes / 720, r * 0.5)} stroke="#b63a4e" strokeWidth={3} /><path d={tip(minutes / 60, r * 0.8)} stroke="#243a45" strokeWidth={2} /><rect x={-2} y={-2} width={4} height={4} fill="#243a45" /></g>;
};

// 도트 눈금. val 0~1
const Gauge: React.FC<{x: number; y: number; w: number; val: number; label: string}> = ({x, y, w, val, label}) => <g transform={`translate(${x} ${y})`}>
  <text x={0} y={-4} fontFamily={FONT} fontWeight={700} fontSize={12} fill="#243a45">{label} {Math.round(val * 100)}%</text>
  <path d={`M0 0h${w}v12H0z`} fill="#243a45" /><path d={`M2 2h${w - 4}v8H2z`} fill="#f4eed8" /><path d={`M2 2h${Math.round((w - 4) * val)}v8H2z`} fill={val > 0.8 ? '#b63a4e' : '#d78265'} />
</g>;

// 결과 종이 + 냄비. stamp = 도장이 찍힌 뒤 지난 프레임(음수면 아직)
const Sign: React.FC<{x: number; y: number; tick: number; stamp: number}> = ({x, y, tick, stamp}) => <g transform={`translate(${x} ${Math.round(y)})`}>
  <path d="M-2 -2h134v158H-2z" fill="#243a45" /><path d="M0 0h130v154H0z" fill="#fff9e2" />
  <text x={65} y={20} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={12} fill="#243a45">{S.title}</text>
  <path d="M10 27h110v2H10z" fill="#243a45" />
  <text x={65} y={52} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={22} fill="#b63a4e">{RESULT}</text>
  {[46, 64, 82].map((sx, k) => <rect key={sx} x={sx} y={66 - ((tick + k) % 4) * 2} width={2} height={6} fill="#a6b8ac" />)}
  <path d="M30 80h70v6H30z" fill="#b63a4e" /><path d="M26 86h78v26H26z" fill="#2b2b3e" /><path d="M32 112h66v5H32z" fill="#2b2b3e" /><path d="M16 88h10v6H16zM104 88h10v6h-10z" fill="#2b2b3e" />
  <path d="M42 81h8v4h-8zM78 81h8v4h-8z" fill="#fff9e2" /><path d="M58 81h8v4h-8z" fill="#5c7f62" />
  {STAMP && stamp >= 0 ? <g transform={`translate(${stamp < 3 ? 2 : 0} 0)`}><path d="M36 122h58v24H36z" fill="none" stroke="#b63a4e" strokeWidth={3} /><text x={65} y={141} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={17} fill="#b63a4e">{STAMP.text}</text></g> : null}
</g>;

export const PixelScene: React.FC<{preview?: boolean}> = ({preview = false}) => {
  const frame = useCurrentFrame();
  const last = STORY_SCENES.length - 1;
  const i = preview ? [0, Math.min(2, last), last][Math.floor((frame % 144) / 48)] : getSceneIndexForFrame(frame);
  const scene = STORY_SCENES[i], len = scene.endFrame - scene.startFrame;
  const p = preview ? (frame % 48) / 47 : clamp((frame - scene.startFrame) / len);
  const lf = Math.round(p * len); // 장면 안에서 지난 프레임
  const tick = Math.floor(frame / 3);
  const id = scene.id;
  // 이 장면에서 지금까지 나온 대사 가운데 마지막 것
  const said = CHAT.filter((c) => c.t >= scene.startSec && c.t < scene.endSec && fr(c.t) - scene.startFrame <= lf);
  const line = said[said.length - 1];
  const wait = beat('wait');
  const m0 = clockMinutes(wait.clock?.from ?? '0:00');
  let m1 = clockMinutes(wait.clock?.to ?? '0:00');
  if (m1 < m0) m1 += 720;
  const g = wait.gauge ?? {label: '', from: 0, to: 1};
  const kWait = ease((p - 0.05) / 0.85);
  const leadX = Math.round(215 - ease(p / 0.45) * 95);
  const stamp = STAMP ? lf - (fr(STAMP.t) - scene.startFrame) : -1;
  return <svg viewBox="0 0 270 480" width="1080" height="1920" style={{display: 'block', background: '#d8d3b4', imageRendering: 'pixelated', shapeRendering: 'crispEdges'}}>
    <PixelRoom warm={id === 'wait'} />
    {id === 'hook' && <>
      {/* 묻기: 주인공이 자리에서 묻는다 */}
      <Chair x={43} y={235} s={2} />
      <PixelActor x={39} y={156} kind="woman" s={3} pose="seat" tick={tick} typing look={1} brow={p > 0.7} />
      <PixelDesk x={12} y={292} w={123} />
      <path d="M117 279h14v8h-14z" fill="#438f89" /><path d={`M128 ${tick % 2 ? 284 : 282}h12v7h-12z`} fill="#f2c4a0" />
    </>}
    {id === 'ask' && <>
      {/* 대답: 두 사람이 차례로 답한다 */}
      <PixelActor x={111} y={196} s={2} kind="lead" pose="stand" tick={tick + 4} look={-1} />
      <Chair x={32} y={259} /><Chair x={193} y={259} />
      <PixelActor x={17} y={157} s={3} kind="woman" pose="seat" tick={tick} look={1} brow={p > 0.5} />
      <PixelActor x={162} y={157} s={3} kind="new" pose="seat" tick={tick + 8} look={-1} />
      <PixelDesk x={-25} y={309} w={130} monitor={false} /><PixelDesk x={160} y={309} w={135} monitor={false} />
    </>}
    {id === 'wait' && <>
      {/* 기다림: 시계가 돌고 눈금이 찬다 */}
      <path d="M0 100h270v220H0z" fill="#e4d6b0" opacity=".35" />
      <Clock x={222} y={64} r={32} minutes={m0 + (m1 - m0) * kWait} />
      <Gauge x={16} y={58} w={150} val={g.from + (g.to - g.from) * kWait} label={g.label} />
      <PixelActor x={47} y={Math.round(119 + ease(p) * 6)} s={6} kind="woman" pose="seat" tick={tick} look={p > 0.5 ? -1 : 0} brow />
      <PixelDesk x={-30} y={364} w={320} monitor={false} />
    </>}
    {id === 'decide' && <>
      {/* 결정: 정하는 사람이 걸어 들어와 한마디 한다 */}
      <Chair x={30} y={254} s={1} /><PixelDesk x={-31} y={276} w={75} />
      <PixelActor x={18} y={176} s={2} kind="woman" pose="seat" tick={tick} look={1} brow={p > 0.3} />
      <PixelActor x={leadX} y={174} s={2} kind={kindOf(LEAD)} pose={p < 0.45 ? 'walk' : 'stand'} tick={tick} look={-1} />
    </>}
    {id === 'punch' && <>
      {/* 결말: 결과 종이가 내려오고 도장이 찍힌다. 두 사람이 답한다 */}
      <Sign x={70} y={104 - (1 - ease(p / 0.12)) * 300} tick={tick} stamp={stamp} />
      <PixelActor x={8} y={226} s={2} kind="woman" pose="stand" tick={tick} look={1} />
      <PixelActor x={202} y={226} s={2} kind="new" pose="stand" tick={tick + 5} look={-1} />
    </>}
    {line ? <MsgWindow who={line.who} text={line.text} show={lf - (fr(line.t) - scene.startFrame)} tick={tick} /> : null}
    {/* 자막 자리 밖의 앞쪽 소품 */}
    <path d="M0 455h58v25H0z" fill="#526c68" /><path d="M4 446h48v9H4z" fill="#9c9271" /><path d="M17 422h5v24h-5zM27 410h5v36h-5zM38 430h4v16h-4z" fill="#5c7f62" />
    <path d="M7 424h13v5H7zM29 416h13v5H29zM13 437h13v5H13zM36 431h13v5H36z" fill="#80a578" />
  </svg>;
};
