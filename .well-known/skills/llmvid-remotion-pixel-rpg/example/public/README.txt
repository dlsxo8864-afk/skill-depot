이 폴더(public)에 두는 파일

audio/   음성(wav·mp3)과 배경음. 파일을 넣고 src/common.tsx 의 NARRATION, MUSIC 에 이름을 적는다.
         예: public/audio/narration.wav  ->  NARRATION = 'audio/narration.wav'
         적지 않으면 소리 없이 렌더한다.

fonts/   자막 글꼴을 고정하고 싶을 때만 CaptionKR-Bold.ttf 라는 이름으로 넣는다.
         없으면 PC 에 설치된 Noto Sans KR, 그다음 맑은 고딕을 쓴다(src/fonts.ts).

이 팩에는 음성·배경음·글꼴 파일이 들어 있지 않다.
