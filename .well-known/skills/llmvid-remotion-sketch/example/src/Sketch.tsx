import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Anime} from './Anime';

// 그림·자막·소리는 모두 Anime.tsx 에 있다. 새 대본은 Anime.tsx 를 고친다(이 파일은 필터만).
// 떨림 세기는 feDisplacementMap 의 scale(13), 떨림 속도는 seed 를 바꾸는 주기(4프레임).
// 손그림 종이판: 같은 장면에 선 떨림과 종이결만 입힌다.
export const Sketch: React.FC = () => {
  const f = useCurrentFrame();
  const seed = Math.floor(f / 4) % 6;
  return (
    <AbsoluteFill style={{background: '#f6efe0'}}>
      <svg width={0} height={0} style={{position: 'absolute'}}>
        <filter id="boil" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.014" numOctaves={2} seed={seed} result="n" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale={13} />
        </filter>
      </svg>
      <AbsoluteFill style={{filter: 'url(#boil) saturate(.68) contrast(1.03) brightness(1.05)'}}><Anime /></AbsoluteFill>
      <AbsoluteFill style={{mixBlendMode: 'multiply', opacity: 0.7}}>
        <svg width={1080} height={1920}>
          <filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves={3} seed={3} /><feColorMatrix values="0 0 0 0 0.95  0 0 0 0 0.91  0 0 0 0 0.82  0 0 0 0.32 0.72" /></filter>
          <rect width={1080} height={1920} filter="url(#paper)" />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
