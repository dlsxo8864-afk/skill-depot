import React, {useEffect, useState} from 'react';
import {
  cancelRender,
  continueRender,
  delayRender,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {Caption} from '@remotion/captions';

export interface CenteredCaptionsProps {
  readonly captions: readonly Caption[];
}

export const CenteredCaptions: React.FC<CenteredCaptionsProps> = ({
  captions,
}) => {
  const [fontLoaded, setFontLoaded] = useState(false);
  const [fontHandle] = useState(() => delayRender('Loading CaptionKR-Bold font'));
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();

  useEffect(() => {
    if (typeof FontFace === 'undefined') {
      setFontLoaded(true);
      continueRender(fontHandle);
      return;
    }

    const font = new FontFace(
      'CaptionKR-Bold',
      `url(${staticFile('fonts/CaptionKR-Bold.ttf')})`,
      {weight: '700', style: 'normal'}
    );

    font
      .load()
      .then((loaded) => {
        document.fonts.add(loaded);
        setFontLoaded(true);
        continueRender(fontHandle);
      })
      .catch((err: unknown) => {
        cancelRender(err);
      });
  }, [fontHandle]);

  const currentMs = (frame / fps) * 1000;
  const activeCaption = captions.find(
    (caption) => currentMs >= caption.startMs && currentMs < caption.endMs
  );

  if (!fontLoaded || !activeCaption) {
    return null;
  }

  return (
    <div
      data-caption-box="true"
      style={{
        position: 'absolute',
        left: (width - 900) / 2,
        bottom: 290,
        width: 900,
        boxSizing: 'border-box',
        pointerEvents: 'none',
      }}
    >
      <div
        data-ep3-caption="true"
        style={{
          width: '100%',
          boxSizing: 'border-box',
          textAlign: 'center',
          whiteSpace: 'pre-line',
          fontFamily: "'CaptionKR-Bold', 'NotoSansKR', sans-serif",
          fontSize: 64,
          fontWeight: 700,
          lineHeight: 1.3,
          color: '#FAFAFA',
          WebkitTextStroke: '3px #111111',
          paintOrder: 'stroke fill',
          textShadow: '0 2px 4px rgba(0, 0, 0, 0.9)',
          wordBreak: 'keep-all',
        }}
      >
        {activeCaption.text}
      </div>
    </div>
  );
};

