import React, { useEffect, useState } from "react";
import { CanvasImage, cancelRender, continueRender, delayRender, staticFile, Still } from "remotion";
import "./thumbnail-template-1.css";

export type HeadlineFont = "blackHan" | "aggro" | "gmarket";

export type ThumbnailTemplate1Props = {
  episode: string;
  line1: string;
  line2: string;
  backgroundSrc: string;
  line1FontSize: number;
  line2FontSize: number;
  line1ScaleX?: number;
  line1ScaleY?: number;
  line2ScaleX?: number;
  line2ScaleY?: number;
  line1Top?: number;
  line2Top?: number;
  headlineFont?: HeadlineFont;
  backgroundVisible: boolean;
  gradientVisible: boolean;
  mastheadText?: string;
  footerText?: string;
};

export const ThumbnailTemplate1: React.FC<ThumbnailTemplate1Props> = ({
  episode,
  line1,
  line2,
  backgroundSrc,
  line1FontSize,
  line2FontSize,
  line1ScaleX = 0.89,
  line1ScaleY = 1.08,
  line2ScaleX = 0.775,
  line2ScaleY = 1.17,
  line1Top = 1318,
  line2Top = 1517,
  headlineFont = "aggro",
  backgroundVisible,
  gradientVisible,
  mastheadText = "회사에선 말 못 한 썰",
  footerText = "사연 재구성",
}) => {
  const [fontHandle] = useState(() => delayRender("Loading local thumbnail fonts"));

  useEffect(() => {
    const fonts = [
      new FontFace("Template1Black", `url("${staticFile("fonts/BlackHanSans-Regular.ttf")}")`, { weight: "400", style: "normal" }),
      new FontFace("Template1Aggro", `url("${staticFile("fonts/SBAggroB.ttf")}")`, { weight: "700", style: "normal" }),
      new FontFace("Template1Gmarket", `url("${staticFile("fonts/GmarketSansBold.otf")}")`, { weight: "700", style: "normal" }),
      new FontFace("Template1Masthead", `url("${staticFile("fonts/MastheadKR-Black.ttf")}")`, { weight: "900", style: "normal" }),
      new FontFace("Template1Regular", `url("${staticFile("fonts/FooterKR-Regular.ttf")}")`, { weight: "400", style: "normal" }),
    ];

    Promise.all(fonts.map((font) => font.load()))
      .then(async (loaded) => {
        loaded.forEach((font) => document.fonts.add(font));
        await document.fonts.ready;
        continueRender(fontHandle);
      })
      .catch((error: unknown) => cancelRender(error instanceof Error ? error : new Error(String(error))));
  }, [fontHandle]);

  const headlineFontFamily =
    headlineFont === "aggro"
      ? "Template1Aggro, sans-serif"
      : headlineFont === "gmarket"
      ? "Template1Gmarket, sans-serif"
      : "Template1Black, sans-serif";

  const src = /^(https?:|data:)/.test(backgroundSrc) ? backgroundSrc : staticFile(backgroundSrc);

  return (
    <div className="t1-container" style={{ backgroundColor: backgroundVisible ? "#07090E" : "transparent" }}>
      {backgroundVisible ? <CanvasImage src={src} className="t1-background" /> : null}
      {gradientVisible ? <div className="t1-bottom-gradient" /> : null}
      <div className="t1-masthead">{mastheadText}</div>
      <div className="t1-badge">{episode}</div>
      <div
        className="t1-headline t1-headline-1"
        style={{ fontSize: line1FontSize, fontFamily: headlineFontFamily, fontWeight: headlineFont === "blackHan" ? 400 : 700, top: line1Top }}
      >
        <span
          style={{
            position: "absolute",
            top: 0,
            left: "50%",
            width: "max-content",
            translate: "-50% 0",
            transformOrigin: "top center",
            scale: `${line1ScaleX} ${line1ScaleY}`,
            lineHeight: 1.0,
          }}
        >
          {line1}
        </span>
      </div>
      <div
        className="t1-headline t1-headline-2"
        style={{ fontSize: line2FontSize, fontFamily: headlineFontFamily, fontWeight: headlineFont === "blackHan" ? 400 : 700, top: line2Top }}
      >
        <span
          style={{
            position: "absolute",
            top: 0,
            left: "50%",
            width: "max-content",
            translate: "-50% 0",
            transformOrigin: "top center",
            scale: `${line2ScaleX} ${line2ScaleY}`,
            lineHeight: 1.0,
          }}
        >
          {line2}
        </span>
      </div>
      <div className="t1-footer">
        <div className="t1-footer-rule" />
        <span>{footerText}</span>
        <div className="t1-footer-rule" />
      </div>
    </div>
  );
};

export const Template1Stills: React.FC = () => (
  <>
    <Still
      id="Template1"
      component={ThumbnailTemplate1}
      width={1080}
      height={1920}
      defaultProps={{
        episode: "EP2",
        line1: "번따 거절했는데",
        line2: "우리 회사 직원?!",
        backgroundSrc: "images/template1/ep2-background.png",
        line1FontSize: 155,
        line2FontSize: 180,
        line1ScaleX: 0.89,
        line1ScaleY: 1.08,
        line2ScaleX: 0.775,
        line2ScaleY: 1.17,
        headlineFont: "aggro",
        backgroundVisible: true,
        gradientVisible: true,
      }}
    />
    <Still
      id="EP1Template1"
      component={ThumbnailTemplate1}
      width={1080}
      height={1920}
      defaultProps={{
        episode: "EP1",
        line1: "해고한 직원한테",
        line2: "고백받음",
        backgroundSrc: "images/template1/ep1-background.png",
        line1FontSize: 155,
        line2FontSize: 260,
        line1ScaleX: 0.89,
        line1ScaleY: 1.08,
        line2ScaleX: 0.95,
        line2ScaleY: 1.18,
        line1Top: 1218,
        line2Top: 1425,
        headlineFont: "aggro",
        backgroundVisible: true,
        gradientVisible: true,
      }}
    />
    <Still
      id="EP2Template1"
      component={ThumbnailTemplate1}
      width={1080}
      height={1920}
      defaultProps={{
        episode: "EP2",
        line1: "번따 거절했는데",
        line2: "우리 회사 직원?!",
        backgroundSrc: "images/template1/ep2-background.png",
        line1FontSize: 155,
        line2FontSize: 180,
        line1ScaleX: 0.89,
        line1ScaleY: 1.08,
        line2ScaleX: 0.775,
        line2ScaleY: 1.17,
        headlineFont: "aggro",
        backgroundVisible: true,
        gradientVisible: true,
      }}
    />
    <Still
      id="EP1Template1Overlay"
      component={ThumbnailTemplate1}
      width={1080}
      height={1920}
      defaultProps={{
        episode: "EP1",
        line1: "해고한 직원한테",
        line2: "고백받음",
        backgroundSrc: "images/template1/ep1-background.png",
        line1FontSize: 155,
        line2FontSize: 260,
        line1ScaleX: 0.89,
        line1ScaleY: 1.08,
        line2ScaleX: 0.95,
        line2ScaleY: 1.18,
        line1Top: 1218,
        line2Top: 1425,
        headlineFont: "aggro",
        backgroundVisible: false,
        gradientVisible: true,
      }}
    />
    <Still
      id="EP2Template1Overlay"
      component={ThumbnailTemplate1}
      width={1080}
      height={1920}
      defaultProps={{
        episode: "EP2",
        line1: "번따 거절했는데",
        line2: "우리 회사 직원?!",
        backgroundSrc: "images/template1/ep2-background.png",
        line1FontSize: 155,
        line2FontSize: 180,
        line1ScaleX: 0.89,
        line1ScaleY: 1.08,
        line2ScaleX: 0.775,
        line2ScaleY: 1.17,
        headlineFont: "aggro",
        backgroundVisible: false,
        gradientVisible: true,
      }}
    />
  </>
);
