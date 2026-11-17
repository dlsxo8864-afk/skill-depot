import {FPS, S, SUBS, TOTAL, fr} from './script';

// 장면 구간과 자막을 대본(script.json)에서 만든다. 장면 하나가 대본의 구간 하나다.
// 이 파일에는 대사가 없다. 대본을 바꾸려면 script.json 을 고친다.
export const STORY_METADATA = {
  title: S.title,
  fps: FPS,
  durationInFrames: TOTAL,
  previewDurationInFrames: 144,
  width: 1080,
  height: 1920,
};
// startFrame·endFrame 은 둘 다 포함이다.
export const STORY_SCENES = S.beats.map((b) => ({id: b.id, name: b.id, startSec: b.start, endSec: b.end, startFrame: fr(b.start), endFrame: fr(b.end) - 1}));
export const STORY_CAPTIONS = SUBS.map(([a, b, text], i) => ({id: `caption-${i + 1}`, text, startFrame: fr(a), endFrame: fr(b) - 1}));
export const getSceneIndexForFrame = (frame: number): number => Math.max(0, STORY_SCENES.findIndex((s) => frame >= s.startFrame && frame <= s.endFrame));
export const getCurrentCaption = (frame: number) => STORY_CAPTIONS.find((c) => frame >= c.startFrame && frame <= c.endFrame) || null;
