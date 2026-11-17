import React from 'react';
import {Audio, staticFile} from 'remotion';
import './fonts';
import {getCurrentCaption} from './StoryData';

// [대본] 음성·배경음 파일. public/ 아래 경로를 적는다(예: 'audio/narration.wav'). 없으면 null — 소리 없이 렌더한다.
export const NARRATION: string | null = null;
export const MUSIC: string | null = null;
const MUSIC_VOLUME = 0.3;

export const SAFE_BOTTOM_CAPTION_STYLE: React.CSSProperties = {
  position: 'absolute',
  left: '50%',
  transform: 'translateX(-50%)',
  bottom: 290,
  width: 900,
  textAlign: 'center',
  zIndex: 90,
  pointerEvents: 'none',
};

export const CaptionBox: React.FC<{frame: number; color?: string; outlineColor?: string}> = ({
  frame,
  color = '#fff',
  outlineColor = '#181e24',
}) => {
  const cap = getCurrentCaption(frame);
  if (!cap) return null;
  return (
    <div style={SAFE_BOTTOM_CAPTION_STYLE}>
      <p
        style={{
          margin: 0,
          padding: '8px 20px',
          fontFamily: 'MotionCaption, sans-serif',
          fontSize: 64,
          fontWeight: 700,
          lineHeight: 1.32,
          color,
          textShadow: '0 4px 12px rgba(0,0,0,.4)',
          letterSpacing: '-0.02em',
          wordBreak: 'keep-all',
          whiteSpace: 'pre-line',
          WebkitTextStroke: `3px ${outlineColor}`,
          paintOrder: 'stroke fill',
        }}
      >
        {cap.text}
      </p>
    </div>
  );
};

export const FilmAudioTrack: React.FC<{enabled?: boolean}> = ({enabled = false}) =>
  enabled ? (
    <>
      {NARRATION ? <Audio src={staticFile(NARRATION)} volume={1} /> : null}
      {MUSIC ? <Audio src={staticFile(MUSIC)} volume={MUSIC_VOLUME} /> : null}
    </>
  ) : null;
