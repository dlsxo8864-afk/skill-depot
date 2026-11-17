import raw from './script.json';

// 대본(script.json)을 읽어 컷들이 쓰기 좋은 꼴로 내놓는다. 이 파일에는 대사가 없다.
// 대본을 바꾸려면 같은 폴더의 script.json 을 고친다(모든 팩이 같은 형식을 쓴다).
export type Chat = {t: number; who: string; text: string};
export type Beat = {
  id: string;
  start: number;
  end: number;
  keyword?: string;
  narration?: string;
  chat?: Chat[];
  clock?: {from: string; to: string};
  gauge?: {label: string; from: number; to: number};
  stamp?: {t: number; text: string};
  result?: string;
};
type Script = {
  title: string;
  fps: number;
  seconds: number;
  frames: number;
  cast: {id: string; name: string}[];
  chat_room?: string;
  beats: Beat[];
  subs: [number, number, string][];
  sfx?: {send?: number[]; buzz?: number[]; hit?: number[]};
};

export const S = raw as unknown as Script;
export const FPS = S.fps;
export const TOTAL = S.frames;
/** 초 → 프레임 */
export const fr = (sec: number): number => Math.round(sec * FPS);
/** 구간 id → 구간. 없으면 빈 구간(길이 0) */
export const beat = (id: string): Beat => S.beats.find((b) => b.id === id) ?? {id, start: 0, end: 0};
export const NAME: Record<string, string> = S.cast.reduce((acc, c) => ({...acc, [c.id]: c.name}), {} as Record<string, string>);
/** 첫 등장인물 = 주인공(휴대폰 주인), 마지막 등장인물 = 정하는 사람 */
export const ME = S.cast[0].id;
export const LEAD = S.cast[S.cast.length - 1].id;
export const ROOM = S.chat_room ?? '';
/** 모든 구간의 대화를 시간순으로 */
export const CHAT: Chat[] = S.beats.reduce((acc, b) => acc.concat(b.chat ?? []), [] as Chat[]).sort((a, b) => a.t - b.t);
export const STAMP = S.beats.reduce((acc, b) => acc ?? b.stamp ?? null, null as Beat['stamp'] | null);
export const RESULT = S.beats.reduce((acc, b) => acc || b.result || '', '');
/** 자막: [시작 초, 끝 초, 문구]. 대본의 줄바꿈 표시(\N)를 실제 줄바꿈으로 바꾼다 */
export const SUBS: [number, number, string][] = S.subs.map(([a, b, t]) => [a, b, t.split('\\N').join('\n')] as [number, number, string]);
export const SFX = {send: (S.sfx?.send ?? []).map(fr), buzz: (S.sfx?.buzz ?? []).map(fr), hit: (S.sfx?.hit ?? []).map(fr)};
/** "11:50" → 0시부터 센 분(12시간 기준) */
export const clockMinutes = (hhmm: string): number => {
  const [h, m] = hhmm.split(':').map(Number);
  return (h % 12) * 60 + m;
};
