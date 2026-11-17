import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export interface ManagerNotificationProps {
  readonly sender: string;
  readonly message: string;
  readonly delaySeconds?: number;
}

export const ManagerNotification: React.FC<ManagerNotificationProps> = ({
  sender,
  message,
  delaySeconds = 0,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const scale = width / 390;
  const logicalHeight = height / scale;

  const delayFrames = Math.round(delaySeconds * fps);
  const animDurationFrames = Math.max(1, Math.round(0.18 * fps));

  const progress = interpolate(
    frame,
    [delayFrames, delayFrames + animDurationFrames],
    [0, 1],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  const translateY = interpolate(progress, [0, 1], [-8, 0]);

  return (
    <>
      {progress > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: '#000000',
            opacity: progress * 0.06,
            pointerEvents: 'none',
            zIndex: 20,
          }}
        />
      )}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 390,
          height: logicalHeight,
          transform: `scale(${scale})`,
          transformOrigin: 'top left',
          pointerEvents: 'none',
          zIndex: 25,
          overflow: 'hidden',
          fontFamily:
            'NotoSansKR, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif',
        }}
      >
        {progress > 0 && (
          <div
            style={{
              position: 'absolute',
              left: 12,
              top: 78,
              width: 366,
              boxSizing: 'border-box',
              borderRadius: 13,
              backgroundColor: '#fcfcfc',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.09)',
              padding: 12,
              opacity: progress,
              transform: `translateY(${translateY}px)`,
              pointerEvents: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <svg
                width="24"
                height="24"
                viewBox="0 0 64 64"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                style={{ flexShrink: 0 }}
              >
                <rect width="64" height="64" rx="18" fill="#FEE500" />
                <path
                  d="M32 17C23.16 17 16 23.37 16 31.25C16 36.14 19.14 40.45 24 42.87L22.5 48.25C22.37 48.72 22.84 49.12 23.24 48.85L29.71 45.14C30.46 45.22 31.22 45.27 32 45.27C40.84 45.27 48 38.9 48 31.02C48 23.27 40.84 17 32 17Z"
                  fill="#3C1E1E"
                />
              </svg>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, flex: 1 }}>
                <span
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color: '#111111',
                    lineHeight: 1.2,
                  }}
                >
                  {sender}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 400,
                    color: '#8e8e93',
                    lineHeight: 1.2,
                  }}
                >
                  개인톡
                </span>
              </div>
            </div>

            <div
              style={{
                marginTop: 8,
                fontSize: 16,
                fontWeight: 400,
                color: '#1c1c1c',
                lineHeight: 1.35,
                whiteSpace: 'pre-line',
                wordBreak: 'keep-all',
              }}
            >
              {message}
            </div>
          </div>
        )}
      </div>
    </>
  );
};
