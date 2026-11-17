import React from 'react';

// Hand-authored pixel shapes. All coordinates live on the 270 x 480 native grid.
const ink='#202733', hair='#252633', skin='#f2c4a0';
export const PixelSheet: React.FC<{x:number;y:number;scale?:number;flat?:boolean}> = ({x,y,scale=1,flat=false}) => <g transform={`translate(${Math.round(x)} ${Math.round(y)}) scale(${scale})`}>
  {flat ? <><polygon points="0,5 19,0 27,8 8,13" fill="#a99e8e"/><polygon points="0,3 19,-2 27,6 8,11" fill="#fff6db"/><path d="M6 4l13 -3M9 7l10 -3" stroke="#97a0a0" strokeWidth="1"/></> : <><rect width="17" height="23" fill="#acb4ac"/><rect x="-1" y="-1" width="17" height="23" fill="#fff8df"/><rect x="2" y="3" width="10" height="2" fill="#6d999d"/><path d="M2 8h11M2 11h9M2 14h10" stroke="#c2c5b4" strokeWidth="1"/><rect x="10" y="18" width="3" height="1" fill="#dc8c6a"/></>}
</g>;

export const PixelActor: React.FC<{x:number;y:number;s?:number;kind?:'woman'|'new'|'lead';pose?:'stand'|'walk'|'seat';tick?:number;reach?:number;carry?:boolean;look?:number;brow?:boolean;typing?:boolean;handTarget?:{x:number;y:number}}> = ({x,y,s=3,kind='woman',pose='stand',tick=0,reach=0,carry=false,look=1,brow=false,typing=false,handTarget}) => {
  const woman=kind==='woman', lead=kind==='lead', walk=pose==='walk', seat=pose==='seat';
  const shirt=woman?'#438f89':lead?'#546b85':'#d78265';
  const dark=woman?'#28635f':lead?'#35495e':'#a95a4e';
  const light=woman?'#78b7a5':lead?'#8294a3':'#efa484';
  const phase=Math.floor(tick)%6, leg=[[-4,4],[-2,2],[0,0],[4,-4],[2,-2],[0,0]][phase];
  const blink=Math.floor(tick)%29>=27;
  const hx=Math.round(handTarget?.x??31+reach*12), hy=Math.round(handTarget?.y??(typing?39+(tick%2):43)-reach*10);
  const eyeShift=look<0?0:1;
  return <g transform={`translate(${Math.round(x)} ${Math.round(y)}) scale(${s})`}>
    <path d="M3 60h28v2H3zM0 61h34v1H0z" fill="#253c40" opacity=".3"/>
    {/* A six-pose walk cycle; the seated pose keeps knees bent under the desk. */}
    {[0,1].map(i=>{
      const px=i?21:11, foot=walk?leg[i]:0;
      return <g key={i}><polygon points={`${px-4},41 ${px+4},41 ${px+4+(seat?7:foot)},${seat?51:59} ${px-3+(seat?7:foot)},${seat?51:59}`} fill={i?'#344352':'#455263'}/>
        <path d={`M${px-2} 44v${seat?5:11}`} stroke="#65717a" strokeWidth="1"/>
        <rect x={px-5+(seat?7:foot)} y={seat?51:58} width="10" height="4" fill={ink}/><rect x={px-3+(seat?7:foot)} y={seat?51:58} width="6" height="1" fill="#879091"/></g>;
    })}
    {/* Back arm / cloth seam. */}
    <polygon points="5,29 10,29 9,43 5,45 2,43 3,33" fill={dark}/>
    <rect x="3" y={walk?42+leg[1]/2:43} width="5" height="5" fill="#dba984"/>
    <polygon points="8,26 24,26 28,31 28,44 6,44 6,31" fill={ink}/>
    <polygon points="9,27 23,27 26,31 26,43 8,43 8,31" fill={shirt}/>
    <rect x="10" y="28" width="3" height="13" fill={light}/><rect x="23" y="31" width="3" height="11" fill={dark}/>
    <path d="M9 42h16M17 33v8" stroke={dark} strokeWidth="1"/>
    <rect x="14" y="23" width="8" height="6" fill="#dca481"/>
    <polygon points="12,27 17,31 14,34 10,28" fill="#f9eccd"/><polygon points="21,27 17,31 21,34 24,28" fill="#fff5d6"/>
    <rect x="18" y="35" width="1" height="1" fill="#e9d9b6"/><rect x="18" y="39" width="1" height="1" fill="#e9d9b6"/>
    {/* Shoulder, forearm and the hand share an endpoint; carried paper follows it. */}
    <polygon points={`25,29 30,30 ${hx+2},${hy-4} ${hx-2},${hy} 24,34`} fill={dark}/>
    <polygon points={`26,30 29,31 ${hx+1},${hy-4} ${hx-2},${hy-1} 25,33`} fill={shirt}/>
    <rect x={hx-3} y={hy-2} width="5" height="5" fill={skin}/><rect x={hx+1} y={hy-1} width="2" height="3" fill="#dba984"/>
    {carry&&<PixelSheet x={hx+1} y={hy-8} scale={.7}/>}
    {/* Stepped silhouette, clustered highlights, shaded face and consistent features. */}
    <polygon points={woman?'5,5 8,2 24,2 28,6 30,12 30,26 25,29 6,28 3,24 3,11':'5,6 8,2 23,2 28,5 29,13 26,22 7,22 4,16'} fill={ink}/>
    <polygon points="8,8 24,7 27,11 27,21 23,26 13,26 8,23 6,16" fill="#d89e7d"/>
    <polygon points="9,8 23,8 25,11 25,21 22,25 13,24 9,21 8,14" fill={skin}/>
    <rect x="9" y="12" width="2" height="6" fill="#ffdbb4"/><rect x="6" y="15" width="3" height="5" fill="#dfab89"/>
    <polygon points={woman?'7,6 11,4 23,4 27,7 27,13 24,12 23,9 17,11 10,10 9,24 6,25 5,20 5,11':'6,6 10,3 22,3 27,6 27,12 23,10 22,8 17,10 9,9 8,15 5,14'} fill={hair}/>
    <path d="M9 6h11M7 8h5" stroke="#51515f" strokeWidth="2"/><path d="M8 5h8" stroke="#747078" strokeWidth="1"/>
    {woman&&<><rect x="25" y="13" width="3" height="12" fill="#30303f"/><rect x="26" y="15" width="1" height="8" fill="#494958"/></>}
    {blink?<path d="M12 16h4M20 16h4" stroke={ink} strokeWidth="1"/>:<>
      <rect x="12" y="14" width="4" height="4" fill="#fff7dd"/><rect x={12+eyeShift} y="14" width="2" height="4" fill={ink}/>
      <rect x="20" y="14" width="4" height="4" fill="#fff7dd"/><rect x={20+eyeShift} y="14" width="2" height="4" fill={ink}/>
      <rect x={12+eyeShift} y="14" width="1" height="1" fill="#b8d1c8"/><rect x={20+eyeShift} y="14" width="1" height="1" fill="#b8d1c8"/>
    </>}
    <path d={`M12 12h4M20 ${brow?10:12}h4`} stroke="#393541" strokeWidth="1"/>
    <rect x="17" y="17" width="2" height="3" fill="#d59a76"/><rect x="11" y="19" width="3" height="2" fill="#e6a48c"/><rect x="22" y="19" width="3" height="2" fill="#e6a48c"/>
    <path d={brow?'M16 23h5':'M16 22h4'} stroke="#a96f65" strokeWidth="1"/>
    {lead&&<><rect x="10" y="13" width="8" height="7" fill="none" stroke="#a2b6b4" strokeWidth="1"/><rect x="19" y="13" width="8" height="7" fill="none" stroke="#a2b6b4" strokeWidth="1"/><path d="M18 15h1" stroke="#a2b6b4"/></>}
  </g>;
};

export const PixelPrintout:React.FC<{x:number;y:number}>=({x,y})=><g transform={`translate(${Math.round(x)} ${Math.round(y)})`}><path d="M0 0h31v31H0z" fill="#aabcb0"/><path d="M-1 -1h31v29H-1z" fill="#fff9e2"/><path d="M3 5h22M3 9h18M3 13h21M3 17h10" stroke="#a6b8ac" strokeWidth="1"/></g>;
export const PixelPrinter:React.FC<{x:number;y:number;s?:number;paper?:boolean;emerge?:number}>=({x,y,s=1,paper=true,emerge=1})=><g transform={`translate(${x} ${y}) scale(${s})`}>
  <polygon points="0,19 15,6 75,6 88,20 88,76 75,85 0,85" fill="#2c4149"/>
  <path d="M4 73h79v44H4z" fill="#b88765"/><path d="M12 82h6v35h-6zM72 82h6v35h-6z" fill="#775849"/><path d="M18 90h54v4H18z" fill="#94674f"/>
  <path d="M3 23h70v57H3z" fill="#e8e0c8"/><polygon points="73,23 84,16 84,72 73,80" fill="#a8b5ad"/><polygon points="3,23 17,10 84,10 73,23" fill="#fbf3d9"/>
  <path d="M14 14h55v6H14z" fill="#75918f"/><path d="M7 29h61v11H7z" fill="#354d59"/><path d="M48 31h15v6H48z" fill="#5aa6a1"/><path d="M51 32h7v1H51z" fill="#aed9b6"/>
  <rect x="11" y="33" width="3" height="3" fill="#d39e54"/><rect x="17" y="33" width="3" height="3" fill="#74ba95"/>
  <path d="M13 47h47v8H13z" fill="#283e49"/><path d="M10 56h52v5H10z" fill="#c8c9b7"/>
  {paper&&<PixelPrintout x={21} y={50-emerge*20}/>}
  <path d="M12 66h49v9H12z" fill="#cec9b5"/><path d="M27 68h19v2H27z" fill="#849994"/><path d="M77 35v25M80 35v25" stroke="#7f9892" strokeWidth="1"/>
</g>;

export const PixelDesk:React.FC<{x:number;y:number;w?:number;monitor?:boolean}>=({x,y,w=115,monitor=true})=><g transform={`translate(${x} ${y})`}>
  <path d={`M0 14h${w}v50H0z`} fill="#a97452"/><path d={`M0 15h${w}v4H0z`} fill="#725341"/><polygon points={`0,14 14,0 ${w+14},0 ${w},14`} fill="#d2a779"/>
  <path d={`M8 20v44M${w-9} 20v44`} stroke="#d2a079" strokeWidth="4"/>
  <rect x={w-34} y="23" width="24" height="30" fill="#906045"/><path d={`M${w-32} 33h19M${w-32} 44h19`} stroke="#624f40" strokeWidth="1"/>
  {[29,40,51].map(n=><rect key={n} x={w-25} y={n-4} width="6" height="1" fill="#e0b985"/>)}
  {monitor&&<g transform={`translate(${w*.53} -41)`}><path d="M2 0h45v36H2z" fill="#243d48"/><path d="M5 3h39v28H5z" fill="#769f9e"/><path d="M8 6h15v22H8z" fill="#486c7c"/><path d="M26 7h14v3H26zM26 13h10v2H26zM26 18h12v2H26z" fill="#bad0b4"/><path d="M20 36h8v11h-8zM12 46h25v3H12z" fill="#324b54"/><path d="M14 47h18" stroke="#688e91" strokeWidth="1"/></g>}
  <polygon points="28,5 59,5 54,11 23,11" fill="#526b71"/><path d="M28 7h26M30 9h21" stroke="#a4b9b0" strokeWidth="1"/>
  <rect x="8" y="-11" width="9" height="15" fill="#f5d4a1"/><rect x="10" y="-10" width="5" height="3" fill="#795b4d"/><path d="M17 -7h3v7h-3" fill="none" stroke="#f5d4a1" strokeWidth="2"/>
</g>;

export const PixelRoom:React.FC<{warm?:boolean}>=({warm=false})=><>
  <rect width="270" height="480" fill={warm?'#d7b58d':'#d8d3b4'}/>
  <path d="M0 0h270v12H0zM0 277h270v11H0z" fill="#959e90"/><path d="M0 13h270M0 281h270" stroke="#eff0ce" strokeWidth="2"/>
  <rect y="288" width="270" height="192" fill="#718d8c"/>
  {Array.from({length:9},(_,i)=><g key={i}><path d={`M0 ${296+i*23}h270`} stroke="#526f74" strokeWidth="1"/><path d={`M${-110+i*53} 288l80 192`} stroke="#5b7779" strokeWidth="1"/></g>)}
  <polygon points="25,99 95,99 250,379 125,379" fill="#f7e8b4" opacity=".18"/>
  {/* Deep window recess, skyline, clouds, blinds, warm sill. */}
  <path d="M19 36h114v114H19z" fill="#63817e"/><path d="M24 41h104v103H24z" fill="#a7c4bc"/>
  <path d="M26 43h99v38H26z" fill="#bdd8c6"/><path d="M34 56h20v4H34zM39 52h10v4H39zM85 62h26v3H85z" fill="#e5e7c7"/>
  <path d="M28 108h13v34H28zM44 88h21v54H44zM72 101h17v41H72zM91 79h20v63H91zM113 105h11v37H113z" fill="#779f9d"/>
  <path d="M47 94h3v4h-3zM54 94h3v4h-3zM95 86h4v4h-4zM104 86h4v4h-4zM95 97h4v4h-4z" fill="#cbd7b8"/>
  <path d="M72 41h5v104h-5zM24 89h104v4H24z" fill="#e9e6c7"/><path d="M18 145h116v7H18z" fill="#bd956c"/>
  {[46,50,54].map(y=><path key={y} d={`M23 ${y}h106`} stroke="#d8dfbd" strokeWidth="2"/>)}
  <path d="M137 42v106h2V42" fill="#9a9d88"/><rect x="136" y="137" width="3" height="8" fill="#b8a37e"/>
  {/* Clock and pinboard have tiny original marks, never readable paperwork. */}
  <path d="M194 34h24v3h4v25h-4v3h-24v-3h-4V37h4z" fill="#66827e"/><rect x="195" y="39" width="22" height="21" fill="#f4e8bf"/><path d="M206 42v9h7" stroke="#735f4c" strokeWidth="2"/>
  <path d="M169 83h82v67h-82z" fill="#b89168"/><path d="M172 86h76v61h-76z" fill="#bba47b"/>
  <g transform="translate(177 95)"><PixelSheet x={0} y={0}/><PixelSheet x={24} y={12}/><PixelSheet x={47} y={-1}/><rect x="5" y="-2" width="3" height="3" fill="#b96450"/><rect x="29" y="10" width="3" height="3" fill="#5c9c8b"/></g>
  {/* Plant, shelf and small objects anchor the room rather than leaving an empty top. */}
  <path d="M239 258h22l-3 28h-16z" fill="#b87857"/><path d="M237 255h26v5h-26z" fill="#dfa16f"/><path d="M249 220h3v36h-3z" fill="#536f51"/>
  <path d="M249 230l-14 -7v-12h8l10 12z" fill="#678c61"/><path d="M250 240l16 -8v-13h-8l-8 12z" fill="#456f53"/><path d="M247 220v-18h7v20z" fill="#86a46b"/>
  <path d="M0 182h32v4H0zM0 225h32v4H0z" fill="#a27e5b"/><path d="M5 160h5v22H5zM11 158h7v24h-7zM20 164h6v18h-6z" fill="#6f8c8a"/><path d="M3 163h2v18H3zM19 161h2v21h-2z" fill="#cc8a67"/>
</>;
