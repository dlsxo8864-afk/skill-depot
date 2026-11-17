import React from 'react';
import {AbsoluteFill, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import './fonts';
import {S, SFX, SUBS} from './script';

// 키네틱 타이포판: 말하는 덩어리마다 큰 글자가 튀어나온다. 1080×1920.
// 글자·시각은 대본(script.json)의 내레이션과 자막 시각에서 만든다. 이 파일에는 대사가 없다.
const INK = '#14121c';
// 음성: 기본은 null(무음). 파일을 public/audio/ 에 두고 'audio/narration.wav' 로 바꾼다.
const NARRATION: string | null = null;
// 효과음(메시지 전송음): 기본은 null. 만드는 법은 SKILL.md '효과음' 절. 예: 'audio/send.wav'. 넣는 때는 대본의 sfx.send
const SFX_SEND: string | null = null;

// ───────── [풀이] 이 팩이 대본을 그리는 방식 ─────────
// 구간마다 바탕색·글자색·강조색. 구간이 더 많으면 처음부터 다시 돌려 쓴다
const PALETTE = [
  {bg: '#ffd84d', fg: INK, hc: '#d6304c'},
  {bg: '#3a64d8', fg: '#fff', hc: '#ffd84d'},
  {bg: '#2e8a8f', fg: '#fff', hc: '#ffd84d'},
  {bg: INK, fg: '#fff', hc: '#ff8a5c'},
  {bg: '#d6304c', fg: '#fff', hc: '#ffd84d'},
];
const MAX_LINE = 7; // 한 줄 글자 수(띄어쓰기 포함). 넘으면 다음 줄로 넘긴다
const LINES_PER_CHUNK = 2; // 한 번에 보이는 줄 수

// 내레이션을 낱말 단위로 줄에 담는다(낱말 하나가 MAX_LINE 보다 길면 그 낱말만 한 줄)
const toLines = (text: string): string[] => {
  const lines: string[] = [];
  text.split(' ').filter(Boolean).forEach((w) => {
    const last = lines[lines.length - 1];
    if (last !== undefined && (last + ' ' + w).length <= MAX_LINE) lines[lines.length - 1] = last + ' ' + w;
    else lines.push(w);
  });
  return lines;
};

type Item = {a: number; lines: string[]; beat: number; hi?: string};
// 구간의 내레이션을 덩어리로 나누고, 그 구간 자막의 시간을 글자 수 비율로 나눠 준다.
// 강조하는 줄: 구간 키워드가 든 줄. 없으면 그 구간의 마지막 줄
const ITEMS: Item[] = [];
S.beats.forEach((b, i) => {
  const sub = SUBS.find(([a]) => a >= b.start && a < b.end);
  const a = sub ? sub[0] : b.start;
  const e = sub ? sub[1] : b.end;
  const lines = toLines(b.narration ?? '');
  const total = lines.join('').length || 1;
  const kw = b.keyword ?? '';
  let done = 0;
  for (let k = 0; k < lines.length; k += LINES_PER_CHUNK) {
    const part = lines.slice(k, k + LINES_PER_CHUNK);
    const lastChunk = k + LINES_PER_CHUNK >= lines.length;
    const hi = part.find((ln) => kw !== '' && ln.indexOf(kw) >= 0) ?? (lastChunk ? part[part.length - 1] : undefined);
    ITEMS.push({a: a + (e - a) * (done / total), lines: part, beat: i, hi});
    done += part.join('').length;
  }
});

export const Kinetic: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const cur = [...ITEMS].reverse().find((x) => t >= x.a) ?? ITEMS[0];
  const start = Math.round(cur.a * fps);
  const pal = PALETTE[cur.beat % PALETTE.length];
  const b = S.beats[cur.beat];
  const beatStart = Math.round(b.start * fps);
  const chip = spring({frame: f - beatStart, fps, config: {damping: 12, stiffness: 200}});
  return (
    <AbsoluteFill style={{background: pal.bg, alignItems: 'center', justifyContent: 'center', fontFamily: 'Head'}}>
      {/* 구간 키워드 칩 */}
      {b.keyword ? <div style={{position: 'absolute', top: 250, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}><div style={{border: `10px solid ${pal.fg}`, color: pal.fg, borderRadius: 70, padding: '6px 56px', fontSize: 96, transform: `scale(${chip})`}}>{b.keyword}</div></div> : null}
      <div style={{textAlign: 'center', lineHeight: 1.12, marginTop: -40}}>
        {cur.lines.map((line, i) => {
          const s = spring({frame: f - start - i * 3, fps, config: {damping: 12, stiffness: 210}});
          const size = line.length <= 4 ? 260 : line.length <= 6 ? 190 : 138;
          const hit = cur.hi === line;
          const wob = hit ? Math.sin((f - start) / 2.2) * interpolate(f - start, [0, 14], [4, 0], {extrapolateRight: 'clamp'}) : 0;
          return (
            <div key={`${cur.a}-${i}`} style={{fontSize: size, color: hit ? pal.hc : pal.fg, opacity: s, transform: `translateY(${(1 - s) * 90}px) scale(${0.8 + s * 0.2}) rotate(${wob}deg)`}}>
              {line}
            </div>
          );
        })}
      </div>
      {NARRATION ? <Audio src={staticFile(NARRATION)} /> : null}
      {SFX_SEND ? SFX.send.map((at) => <Sequence key={at} from={at}><Audio src={staticFile(SFX_SEND)} volume={0.7} /></Sequence>) : null}
    </AbsoluteFill>
  );
};
