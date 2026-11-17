import React from 'react';
import {Sequence, Series, staticFile, useVideoConfig} from 'remotion';
import {Audio, Video} from '@remotion/media';
import type {Caption} from '@remotion/captions';
import {ChatInsert} from './ChatInsert';
import {ManagerNotification} from './EP3Notifications';
import {CenteredCaptions} from './CenteredCaptions';

export const EP3_CAPTIONS: readonly Caption[] = [
  {
    text: '회사 단톡에',
    startMs: 120,
    endMs: 1240,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: 'ㅎㅎㅎ 썼다가',
    startMs: 1240,
    endMs: 2980,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '불려갔어요.',
    startMs: 2980,
    endMs: 4160,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '이직하고 첫',
    startMs: 4360,
    endMs: 5340,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '환영 회식 공지에',
    startMs: 5340,
    endMs: 6560,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '“넵, 알겠습니다”',
    startMs: 6560,
    endMs: 7640,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '하고 붙였거든요.',
    startMs: 7640,
    endMs: 8960,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '그랬더니 팀장님',
    startMs: 9220,
    endMs: 10540,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '개인톡.',
    startMs: 10540,
    endMs: 11340,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '업무 단톡에서',
    startMs: 11560,
    endMs: 12540,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '그런 표현 쓰지 말래요.',
    startMs: 12540,
    endMs: 14440,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '며칠 뒤,',
    startMs: 15720,
    endMs: 16460,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '“감사합니다”에',
    startMs: 16460,
    endMs: 18160,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '스마일 하나 붙였는데…',
    startMs: 18160,
    endMs: 19720,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '“지난번에 말씀드렸죠?”',
    startMs: 19720,
    endMs: 21580,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '전 회사에선\n다들 쓰던 건데요.',
    startMs: 22320,
    endMs: 24140,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '이제 답장 한 줄도\n검열하게 돼요.',
    startMs: 24340,
    endMs: 26440,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
  {
    text: '여긴 웃는 것도\n결재받아요?',
    startMs: 27160,
    endMs: 29280,
    timestampMs: null,
    confidence: null,
    pageBreakAfter: true,
  },
];

export const OfficeStoryEP3: React.FC = () => {
  const {fps} = useVideoConfig();

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        backgroundColor: '#000000',
      }}
    >
      <Series>
        <Series.Sequence durationInFrames={48} name="정면 반응 훅" premountFor={fps}>
          <Video
            src={staticFile('video/hook.mp4')}
            premountFor={fps}
            muted
            playbackRate={1}
            style={{width: 1080, height: 1920, objectFit: 'cover'}}
          />
        </Series.Sequence>

        <Series.Sequence durationInFrames={173} name="ㅎㅎㅎ 전송" premountFor={fps}>
          <ChatInsert
            kind="laugh"
            headerText="팀 단톡방"
            senderText="팀 동료"
            messageText="넵 알겠습니다 ㅎㅎㅎ"
            leadInSeconds={4.5}
            backgroundMode="full"
          />
        </Series.Sequence>

        <Series.Sequence durationInFrames={132} name="첫 번째 경고" premountFor={fps}>
          <ChatInsert
            kind="laugh"
            headerText="팀 단톡방"
            senderText="팀 동료"
            messageText="넵 알겠습니다 ㅎㅎㅎ"
            leadInSeconds={-1}
            backgroundMode="full"
          />
          <ManagerNotification
            sender="팀장님"
            message={'업무 단톡에 ㅎㅎㅎ는 빼주세요.\n잠깐 제 자리로 와주시겠어요?'}
            delaySeconds={0.25}
          />
        </Series.Sequence>

        <Series.Sequence durationInFrames={43} name="책상 측면" premountFor={fps}>
          <Video
            src={staticFile('video/desk.mp4')}
            premountFor={fps}
            muted
            playbackRate={1}
            style={{width: 1080, height: 1920, objectFit: 'cover'}}
          />
        </Series.Sequence>

        <Series.Sequence durationInFrames={77} name="스마일 전송" premountFor={fps}>
          <ChatInsert
            kind="smile"
            headerText="팀 단톡방"
            senderText="팀 동료"
            messageText="감사합니다 :)"
            leadInSeconds={1.5}
            backgroundMode="full"
          />
        </Series.Sequence>

        <Series.Sequence durationInFrames={147} name="두 번째 경고" premountFor={fps}>
          <ChatInsert
            kind="smile"
            headerText="팀 단톡방"
            senderText="팀 동료"
            messageText="감사합니다 :)"
            leadInSeconds={-1}
            backgroundMode="full"
          />
          <ManagerNotification
            sender="팀장님"
            message={'지난번에 말씀드렸죠?\n업무 톡에 웃는 표시는 쓰지 마세요.'}
            delaySeconds={0.08}
          />
        </Series.Sequence>

        <Series.Sequence durationInFrames={100} name="마지막 반응" premountFor={fps}>
          <Video
            src={staticFile('video/reaction.mp4')}
            premountFor={fps}
            muted
            playbackRate={1}
            style={{width: 1080, height: 1920, objectFit: 'cover'}}
          />
        </Series.Sequence>
      </Series>

      <Sequence from={156} durationInFrames={9} name="첫 답장 발송음" premountFor={fps}>
        <Audio src={staticFile('audio/message-send.wav')} premountFor={fps} />
      </Sequence>
      <Sequence from={432} durationInFrames={9} name="감사 인사 발송음" premountFor={fps}>
        <Audio src={staticFile('audio/message-send.wav')} premountFor={fps} />
      </Sequence>

      <Sequence from={0} durationInFrames={720} name="나레이션·중앙자막" premountFor={fps}>
        <Audio src={staticFile('audio/narration.wav')} volume={0.688} premountFor={fps} />
        <CenteredCaptions captions={EP3_CAPTIONS} />
      </Sequence>
    </div>
  );
};

