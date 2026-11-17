import React from 'react';
type Point={x:number;y:number};
const mix=(a:number,b:number,t:number)=>a+(b-a)*t;
const skin='#efc19c';
export const paperHand=(reach:number):Point=>({x:mix(228,303,reach),y:mix(355,264,reach)});
const Segment:React.FC<{a:Point;b:Point;width:number;color:string}>=({a,b,width,color})=>{
  const len=Math.hypot(b.x-a.x,b.y-a.y),nx=-(b.y-a.y)/len*width/2,ny=(b.x-a.x)/len*width/2;
  return <path d={`M${a.x+nx},${a.y+ny} L${b.x+nx*.78},${b.y+ny*.78} Q${b.x+nx},${b.y+ny} ${b.x-nx*.78},${b.y-ny*.78} L${a.x-nx},${a.y-ny} Z`} fill={color} stroke="#223b3b" strokeOpacity=".23" strokeWidth="2.5"/>;
};

export const PaperSheet:React.FC<{x:number;y:number;scale?:number;flat?:boolean;rotate?:number}>=({x,y,scale=1,flat=false,rotate=-5})=><g transform={`translate(${x} ${y}) rotate(${rotate}) scale(${scale})`} filter="url(#card)">
  <path d={flat?'M0 13L104 -8L150 45L44 66Z':'M0 0L95 -3L101 132L3 136Z'} fill="#fffbec" stroke="#d3d0b5" strokeWidth="2"/>
  {flat?<path d="M28 19l68 -13M39 32l65 -13M49 44l42 -9" stroke="#97b0a5" strokeWidth="3"/>:<><path d="M17 25h62M17 46h48M18 66h60M19 87h35" stroke="#a8b5a5" strokeWidth="4"/><rect x="18" y="108" width="23" height="6" fill="#d5a37b"/></>}
</g>;

export const PaperPerson:React.FC<{x:number;y:number;s?:number;kind?:'woman'|'new'|'lead';tick?:number;pose?:'seat'|'walk'|'stand';reach?:number;look?:number;brow?:boolean;carry?:boolean;typing?:boolean;handTarget?:Point}>=({x,y,s=1,kind='woman',tick=0,pose='stand',reach=0,look=0,brow=false,carry=false,typing=false,handTarget})=>{
  const woman=kind==='woman',lead=kind==='lead',shirt=woman?'#4b948b':lead?'#55738b':'#db8a6d',shadow=woman?'#377068':lead?'#3c526d':'#b76756',light=woman?'#7cb9a5':lead?'#88a5ac':'#efb297';
  const blink=tick%44>41;
  const h=handTarget??paperHand(reach), elbow={x:mix(197,h.x,.52)-14,y:mix(219,h.y,.52)+16};
  const steps=[18,10,0,-18,-10,0],step=pose==='walk'?steps[tick%6]:0;
  const headAngle=brow?-3:look*2;
  return <g transform={`translate(${x} ${y}) scale(${s})`}>
    <ellipse cx="137" cy="566" rx="106" ry="15" fill="#283d3a" opacity=".10"/>
    {/* Jointed legs, with a small knee bend on each passing pose. */}
    {[0,1].map(i=>{
      const a={x:i?164:104,y:385},delta=(i?-1:1)*step,b={x:a.x+delta,y:pose==='seat'?434:475},c={x:a.x-delta*.65+(pose==='seat'?43:0),y:pose==='seat'?491:550};
      return <g key={i}><Segment a={a} b={b} width={49} color={i?'#344957':'#445b65'}/><Segment a={b} b={c} width={40} color={i?'#344957':'#445b65'}/><circle cx={b.x} cy={b.y} r="6" fill="#bbab88"/><path d={`M${c.x-20} ${c.y-4}q20 5 39 -2l16 13q-20 9 -57 3z`} fill="#253943"/><path d={`M${c.x-13} ${c.y+10}h36`} stroke="#8d9d98" strokeWidth="3"/></g>;
    })}
    {/* Left sleeve and hand are separate pieces of cardstock. */}
    <Segment a={{x:65,y:223}} b={{x:49-step*.3,y:310}} width={42} color={shadow}/><Segment a={{x:49-step*.3,y:310}} b={{x:57-step*.4,y:365}} width={32} color={shirt}/>
    <path d={`M${45-step*.4} 354q-7 21 9 28q14 2 20 -14l-8 -17z`} fill={skin} stroke="#b1836c" strokeWidth="2"/>
    <path d="M71 196Q133 180 195 197L210 385Q136 399 58 383L62 228Z" fill={shirt} stroke={shadow} strokeWidth="3" filter="url(#card)"/>
    <path d="M78 209l-3 161 18 8 8 -173z" fill={light} opacity=".45"/><path d="M178 202l20 174 -25 3 2 -174z" fill={shadow} opacity=".45"/>
    <path d="M122 160h29l5 40 -35 0z" fill="#dca783"/>
    <path d="M112 191l25 24 -25 30 -23 -43zM156 191l-19 24 25 28 19 -42z" fill="#f7e8c9" stroke="#e3d5b9" strokeWidth="2"/>
    <path d="M137 222v154M72 377q61 8 122 0" stroke={shadow} strokeWidth="2"/>
    {[253,291,329].map(cy=><circle key={cy} cx="141" cy={cy} r="3.5" fill="#e4d5b2"/>)}
    <path d="M163 248l22 -1 -2 32 -22 1z" fill={shadow} opacity=".35"/>
    <Segment a={{x:197,y:219}} b={elbow} width={42} color={shadow}/><Segment a={elbow} b={{x:h.x,y:h.y+(typing?Math.sin(tick)*3:0)}} width={32} color={shirt}/>
    <circle cx={197} cy={219} r="7" fill="#d4bc8d" stroke="#746f50" strokeWidth="2"/><circle cx={elbow.x} cy={elbow.y} r="6" fill="#c6b28b"/>
    <path d={`M${h.x-13} ${h.y-10}q-6 17 4 25q12 5 23 -5l0 -17q-10 -9 -13 1l-2 -9z`} fill={skin} stroke="#ba8d71" strokeWidth="2"/>
    {carry&&<PaperSheet x={h.x+6} y={h.y-38} scale={.6}/>}
    {/* Facial parts retain the same identity and proportions in every shot. */}
    <g transform={`rotate(${headAngle} 136 175)`} filter="url(#card)">
      <path d={woman?'M54 78Q46 1 133 3Q220 4 213 91L211 168Q188 203 62 184Z':'M57 78Q44 6 137 7Q225 2 216 92L203 143L62 136Z'} fill="#29343e" stroke="#202e34" strokeWidth="3"/>
      <path d="M69 63Q140 26 198 66L195 126Q189 172 139 184Q85 176 73 135Z" fill={skin}/>
      <path d="M75 81q-22 -2 -15 29l16 8M194 83q21 -2 15 27l-16 8" fill="#dcab87"/>
      <path d="M81 111q0 42 47 60 -37 -9 -44 -44z" fill="#ffdbaf" opacity=".6"/>
      <path d={woman?'M61 88Q52 35 98 23Q174 -11 204 59L199 84Q173 66 169 43Q144 76 81 68L76 165L59 176Z':'M57 73Q42 35 96 25Q137 -4 160 20Q218 12 211 75L190 64L176 41Q129 72 80 64L72 101Z'} fill="#29343e"/>
      <path d="M77 44Q119 15 163 30M70 57Q85 43 101 43" stroke="#54606a" strokeWidth="7" fill="none" strokeLinecap="round"/>
      {woman&&<path d="M196 89l10 4 -8 70 -13 18 6 -58z" fill="#3b4753"/>}
      <path d={`M91 91q17 -9 31 -1M153 ${brow?80:91}q18 -12 33 -3`} stroke="#424247" strokeWidth="4" fill="none" strokeLinecap="round"/>
      {blink?<path d="M92 110q16 7 28 0M156 110q15 7 28 0" fill="none" stroke="#35404a" strokeWidth="4"/>:<>
        <ellipse cx="108" cy="110" rx="13" ry="16" fill="#fff2d9"/><ellipse cx="170" cy="110" rx="13" ry="16" fill="#fff2d9"/>
        <ellipse cx={108+look*4} cy="111" rx="6.5" ry="12" fill="#33464d"/><ellipse cx={170+look*4} cy="111" rx="6.5" ry="12" fill="#33464d"/>
        <circle cx={106+look*4} cy="106" r="3" fill="#eef2d5"/><circle cx={168+look*4} cy="106" r="3" fill="#eef2d5"/>
      </>}
      <ellipse cx="89" cy="135" rx="11" ry="6" fill="#de9c88" opacity=".6"/><ellipse cx="189" cy="135" rx="10" ry="6" fill="#de9c88" opacity=".6"/>
      <path d="M138 116l-5 19q7 5 13 0" stroke="#c88f71" strokeWidth="3" fill="none" strokeLinecap="round"/>
      <path d={brow?'M124 153q15 -3 29 -1':'M124 151q14 6 29 -1'} stroke="#a36c63" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
      {lead&&<g fill="none" stroke="#9cae9e" strokeWidth="4"><rect x="88" y="94" width="39" height="32" rx="8"/><rect x="150" y="94" width="39" height="32" rx="8"/><path d="M127 105h23"/></g>}
    </g>
  </g>;
};

export const PaperPrinter:React.FC<{x:number;y:number;s?:number;paper?:boolean;emerge?:number}>=({x,y,s=1,paper=true,emerge=1})=><g transform={`translate(${x} ${y}) scale(${s})`} filter="url(#card)">
  <path d="M14 279L310 270L300 425L25 430Z" fill="#ae7f5b"/><path d="M41 307L65 307L62 422L38 424ZM265 297L284 296L277 419L258 421Z" fill="#795a46"/>
  <path d="M0 66L51 19L320 18L348 65L335 278L10 294Z" fill="#d7d6c1" stroke="#99aca2" strokeWidth="3"/>
  <path d="M11 70L321 63L316 272L18 280Z" fill="#f1e9ce"/><path d="M14 68L57 28L323 28L313 65Z" fill="#fff7dc"/>
  <path d="M29 87L299 82L298 127L29 134Z" fill="#425e67"/><rect x="204" y="92" width="73" height="23" rx="3" fill="#70b2a0"/>
  <circle cx="50" cy="109" r="6" fill="#d3a265"/><circle cx="75" cy="109" r="6" fill="#8fc699"/>
  <path d="M51 167L275 161L275 190L51 195Z" fill="#304952"/>
  <path d="M48 235L270 228L268 260L48 265Z" fill="#d6d4bc"/><path d="M125 245L194 242" stroke="#96a69b" strokeWidth="7" strokeLinecap="round"/>
  {paper&&<PaperSheet x={88} y={173-emerge*86} scale={1.4} rotate={-3}/>}
</g>;

export const PaperDesk:React.FC<{x:number;y:number;s?:number;monitor?:boolean}>=({x,y,s=1,monitor=true})=><g transform={`translate(${x} ${y}) scale(${s})`}>
  <path d="M0 54L465 36L454 280L10 293Z" fill="#ae7a55" filter="url(#card)"/><path d="M0 54L52 0L520 -11L465 58Z" fill="#d4ac7c" stroke="#bb9166" strokeWidth="3"/>
  <path d="M30 78L53 77L48 286L27 288ZM412 65L435 64L428 279L408 280Z" fill="#795d48"/>
  <path d="M305 87L410 82L404 245L303 249Z" fill="#996e51"/><path d="M309 134l91 -4M308 188l90 -4" stroke="#775d49" strokeWidth="3"/><path d="M344 112h26M341 164h26M340 216h26" stroke="#e7c392" strokeWidth="5"/>
  {monitor&&<g transform="translate(255 -156) rotate(-2)" filter="url(#card)"><rect width="189" height="155" rx="9" fill="#354e5a"/><rect x="12" y="12" width="165" height="124" rx="4" fill="#8db0aa"/><path d="M24 24h55v96H24z" fill="#597d83"/><path d="M94 29h62M94 49h42M94 70h55M94 91h44" stroke="#d6ddba" strokeWidth="7"/><path d="M80 155h24v38H80zM54 190h78v9H54z" fill="#3c5b64"/></g>}
  <path d="M129 15L253 10L244 37L118 42Z" fill="#59787b"/><path d="M139 23l97 -5M135 31l93 -5" stroke="#a8c1b4" strokeWidth="3"/>
  <g transform="translate(53 -38) rotate(-4)"><path d="M0 0h35v47q-18 8 -33 0z" fill="#f7dbac"/><ellipse cx="18" cy="2" rx="17" ry="5" fill="#7b6150"/><path d="M35 8q26 -1 10 25l-10 0" fill="none" stroke="#f7dbac" strokeWidth="7"/></g>
</g>;

export const PaperRoom:React.FC=()=> <>
  <defs><filter id="card" x="-25%" y="-25%" width="160%" height="160%"><feDropShadow dx="5" dy="9" stdDeviation="5" floodColor="#354331" floodOpacity=".19"/></filter>
    <pattern id="fibers" width="87" height="83" patternUnits="userSpaceOnUse"><path d="M5 17l7 -2M42 11l5 1M23 54l8 -1M67 46l11 2M52 75l4 -1" stroke="#514a3b" strokeWidth="1" opacity=".10"/></pattern></defs>
  <path d="M0 0H1080V1920H0Z" fill="#efe6cb"/>
  <path d="M0 0H1080V1130Q600 1160 0 1120Z" fill="#d8ded0"/>
  <path d="M-10 1150Q510 1180 1090 1148" stroke="#b9ba9e" strokeWidth="15" fill="none"/>
  <path d="M0 1530L1080 1500M0 1800L1080 1750M160 1150L80 1920M610 1150L750 1920" stroke="#d4caac" strokeWidth="3" fill="none"/>
  <g transform="translate(78 139) rotate(-1)" filter="url(#card)"><path d="M0 0L414 5L419 442L3 451Z" fill="#91b2ab"/><path d="M18 19L398 23L398 425L22 432Z" fill="#c4ded1"/>
    <path d="M23 290L91 290L91 427L23 429ZM115 225L187 225L187 426L115 427ZM216 280L279 279L279 424L216 424ZM306 192L379 193L379 423L306 423Z" fill="#9dbfb7"/>
    <path d="M202 21L208 429M20 205L399 210" stroke="#f4f0d6" strokeWidth="13"/>
    <path d="M-9 444L429 435L429 461L-9 472Z" fill="#bda37a"/>
    <path d="M20 49L398 53M20 68L398 72M20 87L398 91" stroke="#e2e6c9" strokeWidth="10"/>
  </g>
  <g transform="translate(682 186) rotate(2)" filter="url(#card)"><path d="M0 0L295 0L300 249L3 253Z" fill="#c9ad7d"/><PaperSheet x={20} y={35} scale={.8}/><PaperSheet x={120} y={80} scale={.8}/><PaperSheet x={206} y={18} scale={.6}/><circle cx="49" cy="30" r="6" fill="#c47c5c"/><circle cx="153" cy="75" r="6" fill="#548f83"/></g>
  <g transform="translate(560 72) rotate(-3)" filter="url(#card)"><circle cx="0" cy="0" r="55" fill="#719c92"/><circle cx="0" cy="0" r="43" fill="#f5eaca"/><path d="M0 -26V0L27 7" stroke="#596a5c" strokeWidth="5" fill="none" strokeLinecap="round"/></g>
  <g transform="translate(925 880)" filter="url(#card)"><path d="M0 130L105 130L89 271L18 268Z" fill="#bf8867"/><path d="M48 139L57 -28" stroke="#6f8a61" strokeWidth="9"/>
    <path d="M51 48Q-23 45 -12 -20Q53 -20 51 48M55 93Q128 78 122 8Q50 18 55 93M56 2Q22 -47 66 -91Q105 -46 56 2" fill="#78a27a"/><path d="M51 48L-4 -9M55 93L109 26M56 2L65 -71" stroke="#a4bd8b" strokeWidth="3" fill="none"/>
  </g>
  <path d="M72 586L408 590L420 622L70 619Z" fill="#f5eaca" opacity=".55"/>
</>;
