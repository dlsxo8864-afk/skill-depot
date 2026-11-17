import React from 'react';
import {useCurrentFrame} from 'remotion';
import {PaperScene} from './PaperScene';
import {CaptionBox, FilmAudioTrack} from './common';

export type StoryFilmProps = {
  audioEnabled?: boolean;
  captionsEnabled?: boolean;
  preview?: boolean;
};

export const StoryFilm: React.FC<StoryFilmProps> = ({
  audioEnabled = false,
  captionsEnabled = true,
  preview = false,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#000000',
      }}
    >
      <PaperScene preview={preview} />
      {captionsEnabled && <CaptionBox frame={frame} />}
      <FilmAudioTrack enabled={audioEnabled} />
    </div>
  );
};
