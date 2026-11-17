import React from 'react';
import {Composition} from 'remotion';
import {StoryFilm} from './StoryFilm';
import {STORY_METADATA} from './StoryData';

// PaperOffice: 전체 길이. 자막을 켜고, common.tsx 에 음성 파일을 적었으면 소리도 넣는다.
// PaperPreview: 6초 미리보기(장면 셋을 2초씩). 자막·소리 없음.
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="PaperOffice"
      component={StoryFilm}
      width={STORY_METADATA.width}
      height={STORY_METADATA.height}
      fps={STORY_METADATA.fps}
      durationInFrames={STORY_METADATA.durationInFrames}
      defaultProps={{preview: false, audioEnabled: true, captionsEnabled: true}}
    />
    <Composition
      id="PaperPreview"
      component={StoryFilm}
      width={STORY_METADATA.width}
      height={STORY_METADATA.height}
      fps={STORY_METADATA.fps}
      durationInFrames={STORY_METADATA.previewDurationInFrames}
      defaultProps={{preview: true, audioEnabled: false, captionsEnabled: false}}
    />
  </>
);
