import React from 'react';
import {registerRoot, Composition, AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {Video, Audio} from '@remotion/media';
import type {Caption} from '@remotion/captions';
import {OfficeStoryEP3} from './OfficeStoryEP3';
import {CenteredCaptions} from './CenteredCaptions';

type Props={video:string;audio:string;captions:Caption[];frames:number};
const MotionCaptions:React.FC<{captions:Caption[]}>=({captions})=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();const active=captions.find(c=>f/fps*1000>=c.startMs&&f/fps*1000<c.endMs);
 const elapsed=active?f-active.startMs/1000*fps:0;
 return <AbsoluteFill style={{transformOrigin:'50% 82%',scale:interpolate(elapsed,[0,3,5],[.97,1.01,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}}><CenteredCaptions captions={captions}/></AbsoluteFill>;
};
const ClayEpisode:React.FC<Props>=({video,audio,captions})=>{
 const {fps}=useVideoConfig();
 return <AbsoluteFill style={{backgroundColor:'#d9d2c7'}}>
 <Video src={staticFile(video)} muted premountFor={fps} style={{width:'100%',height:'100%',objectFit:'cover'}}/>
 <Audio src={staticFile(audio)} premountFor={fps}/>
 <MotionCaptions captions={captions}/>
 </AbsoluteFill>;
};
const Root:React.FC=()=> <>
 <Composition id="OfficeStoryEP3Clay" component={OfficeStoryEP3} width={1080} height={1920} fps={24} durationInFrames={720}/>
 <Composition id="ClayStory" component={ClayEpisode} width={1080} height={1920} fps={24} durationInFrames={616} defaultProps={{video:'media/ep6.mp4',audio:'media/ep6.wav',captions:[],frames:616}} calculateMetadata={({props})=>({durationInFrames:props.frames})}/>
 </>;
registerRoot(Root);
