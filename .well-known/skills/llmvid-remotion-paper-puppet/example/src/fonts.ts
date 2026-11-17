import {continueRender, delayRender, staticFile} from 'remotion';

// 자막 글꼴 'MotionCaption' 을 준비한다.
// 1) public/fonts/CaptionKR-Bold.ttf 가 있으면 그 파일을 쓴다(팩에는 들어 있지 않다).
// 2) 없으면 PC 에 설치된 한글 글꼴을 쓴다.
// 둘 다 안 되어도 렌더는 멈추지 않는다(기본 글꼴로 나오고 경고만 찍는다).
const FILE = 'fonts/CaptionKR-Bold.ttf';

// Windows 의 Noto Sans KR·맑은 고딕만 확인했다. 뒤의 셋(macOS·리눅스 후보)은 확인하지 못했다.
const LOCAL = [
  'Noto Sans KR Bold',
  'Noto Sans KR',
  'Malgun Gothic Bold',
  'Malgun Gothic',
  'Apple SD Gothic Neo Bold',
  'Noto Sans CJK KR Bold',
  'Noto Sans CJK KR',
]
  .map((name) => `local("${name}")`)
  .join(', ');

const tryLoad = async (src: string): Promise<boolean> => {
  try {
    const face = await new FontFace('MotionCaption', src, {weight: '700'}).load();
    document.fonts.add(face);
    return true;
  } catch (err) {
    return false;
  }
};

const handle = delayRender('fonts');

const loadFonts = async (): Promise<void> => {
  try {
    const ok = (await tryLoad(`url("${staticFile(FILE)}")`)) || (await tryLoad(LOCAL));
    if (!ok) {
      console.warn('[fonts] 한글 자막 글꼴을 찾지 못했다. 기본 글꼴로 렌더한다.');
    }
  } catch (err) {
    console.warn('[fonts] 글꼴 로드 중 오류', err);
  }
  continueRender(handle);
};

loadFonts();
