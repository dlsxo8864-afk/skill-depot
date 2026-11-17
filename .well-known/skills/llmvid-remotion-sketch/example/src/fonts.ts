import {continueRender, delayRender, staticFile} from 'remotion';

// 글꼴 로드. 컴포지션 파일이 `import './fonts';` 로 불러온다.
//  - 'Head' : 제목 글꼴 Black Han Sans. public/fonts/BlackHanSans-Regular.ttf (팩에 들어 있다, OFL).
//  - 'KR'   : 본문·자막 글꼴. public/fonts/CaptionKR-Bold.ttf 가 있으면 그 파일을 쓰고,
//             없으면 PC에 깔린 글꼴(Noto Sans KR → 맑은 고딕 → …)로 넘어간다.
// 글꼴 하나가 실패해도 렌더는 멈추지 않는다. 다 실패하면 브라우저 기본 글꼴로 그려지므로
// 스틸을 뽑아 한글이 제대로 나오는지 눈으로 확인한다.

const HEAD_FILE = 'fonts/BlackHanSans-Regular.ttf';
const BODY_FILE = 'fonts/CaptionKR-Bold.ttf';
// 앞의 넷은 Windows 에서 확인했다. 뒤의 셋(macOS·리눅스 후보)은 확인하지 못했다.
const BODY_LOCAL = ['Noto Sans KR Bold', 'Noto Sans KR', 'Malgun Gothic Bold', 'Malgun Gothic', 'Apple SD Gothic Neo Bold', 'Noto Sans CJK KR Bold', 'Noto Sans CJK KR']
  .map((name) => `local("${name}")`)
  .join(', ');

const tryLoad = async (family: string, src: string): Promise<boolean> => {
  try {
    const face = await new FontFace(family, src).load();
    document.fonts.add(face);
    return true;
  } catch (err) {
    return false;
  }
};

const handle = delayRender('fonts');
const loadFonts = async (): Promise<void> => {
  try {
    const head = await tryLoad('Head', `url("${staticFile(HEAD_FILE)}")`);
    const body = (await tryLoad('KR', `url("${staticFile(BODY_FILE)}")`)) || (await tryLoad('KR', BODY_LOCAL));
    if (!head) console.warn(`[fonts] ${HEAD_FILE} 을 읽지 못했다. 제목이 기본 글꼴로 그려진다.`);
    if (!body) console.warn('[fonts] 본문 글꼴(파일·시스템 글꼴)을 찾지 못했다. 본문이 기본 글꼴로 그려진다.');
  } catch (err) {
    console.warn('[fonts] 글꼴 로드 중 오류', err);
  }
  continueRender(handle);
};
loadFonts();
