import React, { useEffect, useState } from 'react';
import {
  AbsoluteFill,
  cancelRender,
  continueRender,
  delayRender,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type ChatInsertKind = 'laugh' | 'smile';
export type BackgroundMode = 'full' | 'transparent';

export type ChatInsertProps = {
  kind?: ChatInsertKind;
  messageText?: string;
  headerText?: string;
  senderText?: string;
  leadInSeconds?: number;
  backgroundMode?: BackgroundMode;
};

let fontsLoadPromise: Promise<void> | null = null;

const loadChatFonts = (): Promise<void> => {
  if (typeof document === 'undefined') {
    return Promise.resolve();
  }
  if (!fontsLoadPromise) {
    fontsLoadPromise = (async () => {
      const regularFont = new FontFace(
        'NotoSansKR',
        `url(${staticFile('fonts/FooterKR-Regular.ttf')})`,
        { weight: '400', style: 'normal' }
      );
      const boldFont = new FontFace(
        'NotoSansKR',
        `url(${staticFile('fonts/CaptionKR-Bold.ttf')})`,
        { weight: '700', style: 'normal' }
      );

      const [loadedRegular, loadedBold] = await Promise.all([
        regularFont.load(),
        boldFont.load(),
      ]);

      document.fonts.add(loadedRegular);
      document.fonts.add(loadedBold);
    })();
  }
  return fontsLoadPromise;
};

export const getSendFrame = (leadInSeconds: number, fps: number): number => {
  return Math.round(leadInSeconds * fps);
};

export const ChatInsert: React.FC<ChatInsertProps> = ({
  kind = 'laugh',
  messageText,
  headerText = '팀 단톡방',
  senderText = '팀 동료',
  leadInSeconds = 0.12,
  backgroundMode = 'full',
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const [fontHandle] = useState(() => delayRender('Loading chat insert fonts'));

  useEffect(() => {
    if (typeof document === 'undefined') {
      return;
    }
    loadChatFonts()
      .then(() => {
        continueRender(fontHandle);
      })
      .catch((error: unknown) => {
        cancelRender(
          error instanceof Error ? error : new Error(String(error))
        );
      });
  }, [fontHandle]);

  const scale = width / 390;
  const logicalHeight = height / scale;

  const isLaugh = kind === 'laugh';
  const defaultMessage = isLaugh ? '넵 알겠습니다 ㅎㅎㅎ' : '감사합니다 :)';
  const outgoingText = messageText || defaultMessage;
  const isFull = backgroundMode === 'full';

  const isPreSent = leadInSeconds < 0;
  const sendFrame = Math.round(leadInSeconds * fps);
  const typingDurationFrames = Math.max(1, Math.round(0.85 * fps));
  const typingStartFrame = Math.max(0, sendFrame - typingDurationFrames);

  let draftText = '';
  let showCaret = false;
  let bubbleOpacity = 0;
  let bubbleScale = 0.97;
  let bubbleTranslateY = 6;
  let isBubbleVisible = false;

  if (isPreSent) {
    isBubbleVisible = true;
    bubbleOpacity = 1;
    bubbleScale = 1;
    bubbleTranslateY = 0;
  } else {
    if (frame >= typingStartFrame && frame < sendFrame) {
      const elapsed = frame - typingStartFrame;
      const total = Math.max(1, sendFrame - typingStartFrame);
      const ratio = Math.min(1, Math.max(0, (elapsed + 1) / total));
      const charCount = Math.min(
        outgoingText.length,
        Math.max(1, Math.floor(ratio * outgoingText.length))
      );
      draftText = outgoingText.slice(0, charCount);
      showCaret = true;
    }

    if (frame >= sendFrame) {
      isBubbleVisible = true;
      const animDurationFrames = Math.max(1, Math.round(0.18 * fps));
      const progress = interpolate(
        frame,
        [sendFrame, sendFrame + animDurationFrames],
        [0, 1],
        {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        }
      );
      const eased = Math.sin((progress * Math.PI) / 2);
      bubbleOpacity = eased;
      bubbleScale = 0.97 + 0.03 * eased;
      bubbleTranslateY = 6 * (1 - eased);
    }
  }

  const hasDraft = draftText.length > 0;

  const renderOutgoingBubble = () => {
    if (!isBubbleVisible) {
      return null;
    }
    return (
      <div
        style={{
          position: 'relative',
          backgroundColor: '#fee500',
          color: '#1a1a1a',
          fontSize: 17,
          lineHeight: 1.4,
          fontWeight: 400,
          padding: '10px 12px',
          borderRadius: 9,
          maxWidth: 282,
          wordBreak: 'keep-all',
          whiteSpace: 'nowrap',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.04)',
          opacity: bubbleOpacity,
          transform: `translateY(${bubbleTranslateY}px) scale(${bubbleScale})`,
          transformOrigin: 'top right',
        }}
      >
        {outgoingText}
        <div
          style={{
            position: 'absolute',
            top: 0,
            right: -4,
            width: 0,
            height: 0,
            borderTop: '5px solid #fee500',
            borderRight: '5px solid transparent',
          }}
        />
      </div>
    );
  };

  return (
    <AbsoluteFill
      style={{
        backgroundColor: isFull ? '#b2c7d9' : 'transparent',
        fontFamily:
          'NotoSansKR, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: 390,
          height: logicalHeight,
          transform: `scale(${scale})`,
          transformOrigin: 'top left',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* iOS-Style Status Bar */}
        {isFull && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 16px',
              boxSizing: 'border-box',
              zIndex: 10,
            }}
          >
            <span
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: '#111111',
                letterSpacing: '-0.01em',
              }}
            >
              9:41
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <svg width="17" height="11" viewBox="0 0 17 11" fill="none">
                <rect x="0" y="8" width="3" height="3" rx="0.5" fill="#111111" />
                <rect x="4.5" y="5.5" width="3" height="5.5" rx="0.5" fill="#111111" />
                <rect x="9" y="3" width="3" height="8" rx="0.5" fill="#111111" />
                <rect x="13.5" y="0.5" width="3" height="10.5" rx="0.5" fill="#111111" />
              </svg>
              <svg width="15" height="11" viewBox="0 0 15 11" fill="none">
                <path d="M0.5 2.5C4.5 -0.8 10.5 -0.8 14.5 2.5" stroke="#111111" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M3 5.5C5.8 3.2 9.2 3.2 12 5.5" stroke="#111111" strokeWidth="1.5" strokeLinecap="round" />
                <path d="M5.5 8.5C6.7 7.5 8.3 7.5 9.5 8.5" stroke="#111111" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <svg width="22" height="11" viewBox="0 0 22 11" fill="none">
                <rect x="0.75" y="0.75" width="18" height="9.5" rx="2.5" stroke="#111111" strokeWidth="1.2" />
                <rect x="2.5" y="2.5" width="13" height="6" rx="1.5" fill="#111111" />
                <path d="M20 3.5V7.5" stroke="#111111" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
            </div>
          </div>
        )}

        {/* Navigation Bar */}
        {isFull && (
          <div
            style={{
              position: 'absolute',
              top: 32,
              left: 0,
              right: 0,
              height: 52,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 14px',
              boxSizing: 'border-box',
              zIndex: 10,
            }}
          >
            <div style={{ width: 21, height: 21, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg
                width="21"
                height="21"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#111111"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </div>

            <div
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                textAlign: 'center',
                pointerEvents: 'none',
                fontSize: 17,
                fontWeight: 600,
                color: '#111111',
                letterSpacing: '-0.02em',
              }}
            >
              {headerText}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <svg
                width="21"
                height="21"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#111111"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="7" />
                <line x1="21" y1="21" x2="16.5" y2="16.5" />
              </svg>
              <svg
                width="21"
                height="21"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#111111"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="4" y1="6" x2="20" y2="6" />
                <line x1="4" y1="12" x2="20" y2="12" />
                <line x1="4" y1="18" x2="20" y2="18" />
              </svg>
            </div>
          </div>
        )}

        {/* Conversation Area */}
        {isLaugh ? (
          <div
            style={{
              position: 'absolute',
              top: 118,
              left: 12,
              right: 12,
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box',
            }}
          >
            {/* Incoming Message Row */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <div
                style={{
                  width: 35,
                  height: 35,
                  borderRadius: 17.5,
                  backgroundColor: '#cbd5e1',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
                    fill="#ffffff"
                  />
                </svg>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                <div
                  style={{
                    fontSize: 12,
                    color: '#4a5568',
                    marginBottom: 4,
                    fontWeight: 400,
                    letterSpacing: '-0.01em',
                  }}
                >
                  {senderText}
                </div>
                <div
                  style={{
                    backgroundColor: '#ffffff',
                    color: '#1a1a1a',
                    fontSize: 17,
                    lineHeight: 1.4,
                    fontWeight: 400,
                    padding: '10px 12px',
                    borderRadius: 9,
                    maxWidth: 303,
                    boxSizing: 'border-box',
                    wordBreak: 'keep-all',
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.04)',
                  }}
                >
                  환영 회식 안내드립니다.
                </div>
              </div>
            </div>

            {/* Outgoing Reply Below Incoming with 16px Gap */}
            <div
              style={{
                marginTop: 16,
                display: 'flex',
                justifyContent: 'flex-end',
              }}
            >
              {renderOutgoingBubble()}
            </div>
          </div>
        ) : (
          <div
            style={{
              position: 'absolute',
              top: 218,
              right: 12,
              display: 'flex',
              justifyContent: 'flex-end',
              boxSizing: 'border-box',
            }}
          >
            {renderOutgoingBubble()}
          </div>
        )}

        {/* Native Footer Composer & Home Indicator */}
        {isFull && (
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 78,
              backgroundColor: '#f8f9fa',
              borderTop: '1px solid #d4dbe2',
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box',
              zIndex: 10,
            }}
          >
            {/* Composer row 54px */}
            <div
              style={{
                height: 54,
                display: 'flex',
                alignItems: 'center',
                padding: '0 10px',
                gap: 8,
                boxSizing: 'border-box',
              }}
            >
              <div
                style={{
                  width: 22,
                  height: 22,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#6b7280"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </div>

              <div
                style={{
                  flex: 1,
                  height: 36,
                  backgroundColor: '#ffffff',
                  borderRadius: 18,
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0 12px',
                  boxSizing: 'border-box',
                  overflow: 'hidden',
                }}
              >
                <span
                  style={{
                    fontSize: 15,
                    color: '#1a1a1a',
                    whiteSpace: 'nowrap',
                    lineHeight: 1.2,
                  }}
                >
                  {draftText}
                </span>
                {showCaret && (
                  <span
                    style={{
                      display: 'inline-block',
                      width: 1.5,
                      height: 16,
                      backgroundColor: '#3b82f6',
                      marginLeft: 1,
                    }}
                  />
                )}
              </div>

              {hasDraft && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#94a3b8"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                    <line x1="9" y1="9" x2="9.01" y2="9" strokeWidth="2.5" />
                    <line x1="15" y1="9" x2="15.01" y2="9" strokeWidth="2.5" />
                  </svg>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      backgroundColor: '#fee500',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <svg
                      width="21"
                      height="21"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#1a1a1a"
                      strokeWidth="2.2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <line x1="12" y1="19" x2="12" y2="5" />
                      <polyline points="5 12 12 5 19 12" />
                    </svg>
                  </div>
                </div>
              )}
            </div>

            {/* Home area 24px */}
            <div
              style={{
                height: 24,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  width: 134,
                  height: 5,
                  backgroundColor: '#000000',
                  borderRadius: 2.5,
                }}
              />
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
