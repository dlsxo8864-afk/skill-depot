import React from 'react';
import {Composition} from 'remotion';
import {FPS, TOTAL} from './script';
import {Sketch} from './Sketch';
import {Anime} from './Anime';

// 길이와 fps 는 대본(script.json)에서 읽는다.
const base = {width: 1080, height: 1920, fps: FPS, durationInFrames: TOTAL};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Sketch" component={Sketch} {...base} />
    <Composition id="Anime" component={Anime} {...base} />
  </>
);
