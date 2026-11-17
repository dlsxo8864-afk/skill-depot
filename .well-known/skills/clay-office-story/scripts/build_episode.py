"""Authored story director. New stories require beats, not just replacement text."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import clay_lib as g
from build_clay import reset_scene

def smooth(p):
    p=max(0,min(1,p));return p*p*(3-2*p)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ep',type=int,choices=[4,5,6],required=True);ap.add_argument('--proofs',action='store_true')
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=ROOT/'episodes'/f'ep{args.ep}'
    tl=json.loads((out/'timeline.json').read_text(encoding='utf-8'));cfg=json.loads((ROOT/'characters.json').read_text(encoding='utf-8'))
    reset_scene();g.configure_render_settings(1080,1920,32);s=bpy.context.scene;s.render.fps=24;s.frame_start=1;s.frame_end=tl['frames']
    g.setup_studio_environment();col=g.get_or_create_collection('Office_Set');props=g.get_or_create_collection('Story_Props')
    mat=lambda n,c:g.create_clay_material(n,(*c,1),roughness=.65)
    wood=mat('desk_oak',(.48,.32,.18));cream=mat('printer_ivory',(.75,.76,.70));dark=mat('navy_objects',(.045,.07,.10));paper=mat('blank_paper',(.92,.90,.82));green=mat('leaf',(.16,.31,.19))
    box=lambda n,sz,loc,m,**kw:g.create_beveled_box(n,sz,location=loc,material=m,collection=col,bevel_width=.018,**kw)
    # Compact open office, visible desk/laptop/plant silhouettes, no lettering.
    box('floor',(8,7,.10),(0,0,-.05),mat('floor',(.64,.58,.48)))
    box('rear_wall',(8,.08,3.4),(0,2.9,1.7),mat('wall',(.65,.71,.66)))
    box('window_frame',(1.5,.06,1.1),(-1.4,2.82,1.7),cream)
    box('window_glass',(1.35,.02,.95),(-1.4,2.77,1.7),mat('window',(.35,.57,.64)))
    for x in [-1.4]:box('window_bar',(.035,.05,1),(x,2.73,1.7),cream)
    for i,(x,y) in enumerate([(-.65,.30),(.85,.30),(1.0,1.8)]):
        box(f'desk_{i}',(1.05,.52,.06),(x,y-.50,.70),wood)
        for dx in [-.44,.44]:box(f'desk_{i}_leg{dx}',(.055,.43,.68),(x+dx,y-.50,.34),dark)
        box(f'chair_{i}',(.37,.34,.05),(x,y,.405),dark)
        box(f'chair_{i}_back',(.36,.05,.33),(x,y+.18,.59),dark)
        box(f'laptop_{i}',(.36,.24,.02),(x-.08,y-.5,.745),dark)
        box(f'laptop_{i}_screen',(.36,.025,.22),(x-.08,y-.62,.86),dark)
    for i in range(4):
        box(f'shelf_{i}',(.70,.25,.035),(-.1,2.70,.7+i*.32),wood)
        for j in range(3):box(f'book_{i}_{j}',(.09,.16,.20),(-.32+j*.12,2.68,.82+i*.32),mat(f'bookmat{i}{j}',[(.22,.40,.43),(.58,.34,.23),(.77,.64,.33)][j]))
    g.create_cylinder('plantpot',.16,.25,location=(2.05,1.9,.125),material=wood,collection=col)
    for i in range(5):
        a=i*math.tau/5;g.create_sphere(f'leaf_{i}',.12,location=(2.05+math.cos(a)*.13,1.9+math.sin(a)*.13,.43),scale=(.6,.5,1.8),material=green,collection=col)
    # Separate compact home corner for the weekend beat; camera moves by hard cut.
    box('home_floor',(5,5,.10),(8,0,-.05),mat('homefloor',(.67,.53,.40)))
    box('home_wall',(5,.10,3),(8,2,1.5),mat('homewall',(.76,.65,.54)))
    box('home_sofa',(1.6,.55,.36),(8,.45,.22),mat('sofa',(.42,.53,.49)))
    box('home_sofaback',(1.6,.16,.60),(8,.72,.54),mat('sofaback',(.34,.46,.42)))
    box('home_table',(.45,.45,.035),(8.9,.15,.48),wood)
    box('home_tableleg',(.07,.07,.47),(8.9,.15,.235),wood)
    g.create_cylinder('home_pottery',.055,.11,location=(8.9,.15,.55),material=cream,collection=col)
    lamp_data=bpy.data.lights.new('home_softbox','AREA');lamp_data.energy=280 if args.ep==4 else 0;lamp_data.shape='DISK';lamp_data.size=4
    lamp=bpy.data.objects.new('home_softbox',lamp_data);s.collection.objects.link(lamp);lamp.location=(7,-2,3)
    lamp.rotation_euler=(Vector((8,.4,1))-lamp.location).to_track_quat('-Z','Y').to_euler()
    # Story objects are separately controlled for ownership and contacts.
    box('printer_stand',(.62,.54,.48),(-1.65,-.10,.24),wood)
    box('printer',(.60,.43,.22),(-1.65,-.10,.59),cream)
    box('printer_top',(.53,.38,.045),(-1.65,-.10,.72),dark)
    box('printer_tray',(.38,.25,.025),(-1.65,-.43,.50),dark)
    active=g.create_beveled_box('active_paper',(.25,.20,.009),location=(-1.65,-.43,.521),material=paper,collection=props,bevel_width=.001)
    phone=g.create_beveled_box('phone',(.075,.015,.145),material=dark,collection=props,bevel_width=.008)
    gift1=g.create_beveled_box('gift_requested',(.16,.13,.18),material=mat('gift_peach',(.75,.42,.28)),collection=props,bevel_width=.012)
    gift2=g.create_beveled_box('gift_extra',(.13,.12,.15),material=mat('gift_green',(.29,.48,.39)),collection=props,bevel_width=.012)
    figs=[g.build_character_mesh(cid,cfg['characters'][cid],s.collection) for cid in tl['cast']]
    expr=cfg['expressions']; default=[(-.65,.30,0),(.85,.30,0),(1.0,1.8,0)]
    cameras=[]
    for i,shot in enumerate(tl['scenes']):
        cam=g.create_camera('Shot_'+shot['id'],(1,-3,1.8),(-.65,.30,1.0),50)
        cam.data.type='ORTHO';cam.data.ortho_scale=2.0
        marker=s.timeline_markers.new(shot['id'],frame=shot['startFrame']+1);marker.camera=cam;cameras.append(cam)
    s.camera=cameras[0]
    # Animation state stored at every second frame and both sides of every cut.
    keys=sorted(set(range(1,tl['frames']+1,2))|{tl['frames']}|{x['startFrame']+1 for x in tl['scenes']}|{x['endFrame'] for x in tl['scenes']})
    for frame in keys:
        f=frame-1;idx=next(i for i,x in enumerate(tl['scenes']) if x['startFrame']<=f<x['endFrame']);shot=tl['scenes'][idx]
        u=(f-shot['startFrame'])/max(1,shot['endFrame']-shot['startFrame']-1);beat=shot['id'];ease=smooth(u*2)
        pos=[Vector(x) for x in default];yaw=[0.,0.,0.];hips=[.51,.51,.51];expressions=['neutral']*3
        heads=[(0,0,0)]*3;hands=[None]*3;feet=[None]*3
        phone.location=(0,0,-8);gift1.location=(0,0,-8);gift2.location=(0,0,-8);active.location=(-1.65,-.43,.521);active.rotation_euler=(0,0,0)
        focus=0;wide=False;target=Vector((-.65,.30,1.04));scale=1.65;camoffset=Vector((.42,-3,1.0))
        for i in range(3):hands[i]=[pos[i]+Vector((-.19,-.36,.79)),pos[i]+Vector((.19,-.36,.79))]
        if args.ep==4:
            if beat in ['phone_check','weekend_ping','awkward']:
                expressions[0]='puzzled' if beat=='phone_check' else 'awkward';heads[0]=(.08,0,-.18*ease)
                phone.location=pos[0]+Vector((.15,-.27,.94));hands[0][1]=phone.location+Vector((.02,.015,-.045))
                if beat=='weekend_ping':
                    pos[0]=Vector((8,.40,0));hips[0]=.55;target=Vector((8,.40,1.15));scale=1.35
                    hands[0]=[pos[0]+Vector((-.20,-.12,.55)),pos[0]+Vector((.15,-.23,.92))]
                    phone.location=hands[0][1]+Vector((-.02,-.015,.045))
            elif beat=='collaborate':
                pos[1]=Vector((.02,.35,0));hips[1]=.64;heads[0]=(0,0,-.15);heads[1]=(.12,0,.20);wide=True
                hands[1]=[pos[1]+Vector((-.18,-.2,.76)),pos[1]+Vector((.18,-.2,.76))]
            elif beat=='gift_reveal':
                gift1.location=(.66,-.49,.84);gift2.location=(1.,-.48,.82);target=Vector((.83,-.49,.88));scale=1.15;camoffset=Vector((.4,-2,1.2))
            elif beat=='group_invite':
                wide=True;expressions[0]='awkward';heads[0]=(0,0,-.30);hands[0][0]=pos[0]+Vector((-.33,-.14,.95));heads[1]=(0,0,.25)
            elif beat=='confide':
                pos[2]=Vector((.05,.38,0));pos[1]=Vector((4,0,0));hips[2]=.64;heads[0]=(0,0,-.22);heads[2]=(0,0,.25);wide=True;expressions[0]='puzzled'
                hands[2]=[pos[2]+Vector((-.18,-.2,.76)),pos[2]+Vector((.18,-.2,.76))]
                hands[1]=[pos[1]+Vector((-.18,-.2,.76)),pos[1]+Vector((.18,-.2,.76))]
        elif args.ep==5:
            if beat in ['guilty','guilty_close','resolve']:
                expressions[0]='ashamed';heads[0]=(.13*ease,0,.10)
                if beat=='resolve': heads[0]=(.17*(1-ease),0,0)
            elif beat=='two_desks':wide=True;heads[0]=(0,0,-.30);expressions[0]='awkward'
            elif beat=='interview':
                pos[1]=Vector((4,0,0));pos[2]=Vector((.08,.35,0));hips[2]=.64;yaw[2]=.65;heads[0]=(0,0,-.28);expressions[0]='ashamed';target=Vector((-.33,.30,1.03));scale=2.8
                hands[1]=[pos[1]+Vector((-.2,-.15,.76)),pos[1]+Vector((.2,-.15,.76))]
                hands[2]=[pos[2]+Vector((-.2,-.15,.76)),pos[2]+Vector((.2,-.15,.76))]
            elif beat=='junior_work':focus=1;target=Vector((.85,.30,1.04));heads[1]=(.10,0,0);hands[1][1]+=Vector((0,-.025*math.sin(u*math.pi*2),0))
            elif beat=='greeting':wide=True;expressions[0]='ashamed';expressions[1]='happy';heads[0]=(.13,0,.1);heads[1]=(0,0,.35);hands[1][0]=pos[1]+Vector((-.31,-.10,1.05))
        else:
            if beat in ['hook','glance','response','settle']:
                expressions[0]='puzzled' if beat in ['hook','glance'] else 'annoyed' if beat=='response' else 'awkward';heads[0]=(0,.035,-.3*ease if beat!='settle' else -.25*(1-ease))
                if beat=='hook':target=Vector((-1.15,.05,.9));scale=3.6
                if beat=='settle':active.location=(0,0,-8)
            elif beat=='flashback':
                # Explicit handoff to lead: sheet rests on his desk, narrator reaches it.
                pos[0]=Vector((.17,1.15,0));hips[0]=.64;yaw[0]=-.50
                active.location=Vector((.54,1.28,.745));hands[0][1]=active.location+Vector((-.06,-.025,.035));target=Vector((.65,1.3,1.0));scale=3.0;heads[2]=(.12,0,.35);pos[1]=Vector((4,0,0))
            elif beat=='newcomer':
                focus=1;target=Vector((.85,.30,1.04));expressions[1]='happy';heads[1]=(0,0,.35*ease)
            elif beat=='walk':
                # Ellipsis cut to the clear front aisle, no walking through furniture.
                start=Vector((.90,-1.05,0));end=Vector((-1.30,-.75,0));progress=smooth(u/.72);pos[1]=start.lerp(end,progress);hips[1]=.64;yaw[1]=-math.pi/2
                steps=5
                foot=[]
                for side,phase in [(-1,0),(1,.5)]:
                    q=progress*steps+phase;cycle=math.floor(q);ph=q-cycle
                    tp=max(0,min(1,(cycle+smooth((ph-.5)*2)-phase)/steps))
                    spot=start.lerp(end,tp)+Vector((0,-side*.11,.024+.075*math.sin(math.pi*max(0,(ph-.5)*2))))
                    foot.append(spot)
                feet[1]=foot;reach=smooth((u-.72)/.18);hips[1]-=.04*reach;yaw[1]=-math.pi/2-.65*reach
                if u>.72:
                    for fi,side in enumerate([-1,1]):
                        standing=pos[1]+Quaternion((0,0,1),yaw[1])@Vector((side*.11,-.015,.024))
                        feet[1][fi]=foot[fi].lerp(standing,reach)
                hands[1]=[pos[1]+Vector((-.1,.18,.79)),pos[1]+Vector((.1,.18,.79))]
                hands[1][1]=hands[1][1].lerp(Vector((-1.65,-.45,.55)),reach)
                if u>.90:
                    active.location+=Vector((.18,0,.17))*smooth((u-.9)/.1)
                    hands[1][1]=active.location+Vector((.03,-.02,.025))
                target=Vector((.30,-.45,.95)).lerp(Vector((-1.40,-.40,.95)),progress);scale=3.9;camoffset=Vector((.15,-3,1.1)).lerp(Vector((-2.4,-2.0,1.1)),progress)
        if wide:target=Vector((.1,.30,.95));scale=4.8;camoffset=Vector((.2,-3,1.2))
        for i,fig in enumerate(figs):
            g.pose_actor(fig,tuple(pos[i]),yaw[i],hips[i],hands[i],feet[i]);g.apply_expression(fig,expressions[i],expr);fig['head'].rotation_euler=heads[i]
            # One short blink per beat; fixed torso, no chest bounce.
            blink=1.-.92*max(0,1-abs(u-.58)/.045)
            for side in ['L','R']:fig['eye_'+side].scale.z*=blink
            for key,obj in fig.items():
                if not isinstance(obj,bpy.types.Object):continue
                paths=['location','scale','rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_euler']
                for prop in paths:obj.keyframe_insert(data_path=prop,frame=frame)
        cam=cameras[idx];cam.data.ortho_scale=scale;cam.location=target+camoffset
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.keyframe_insert(data_path='location',frame=frame)
        cam.keyframe_insert(data_path='rotation_euler',frame=frame)
        cam.data.keyframe_insert(data_path='ortho_scale',frame=frame)
        for obj in [phone,gift1,gift2,active]:
            obj.keyframe_insert(data_path='location',frame=frame);obj.keyframe_insert(data_path='rotation_euler',frame=frame)
    # Prevent interpolation across camera cuts from changing who holds each prop.
    cuts={x['endFrame'] for x in tl['scenes']}
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:key.interpolation='CONSTANT' if round(key.co.x) in cuts else 'LINEAR'
    s.frame_set(1);s.camera=cameras[0];bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
    if args.proofs:
        proof=out/'proofs';proof.mkdir(exist_ok=True);s.render.resolution_percentage=50
        for shot in tl['scenes']:
            frame=round((shot['startFrame']+shot['endFrame'])/2)+1;s.frame_set(frame);s.render.filepath=str(proof/(shot['id']+'.png'));bpy.ops.render.render(write_still=True)
    print(json.dumps({'status':'completed','episode':args.ep,'frames':tl['frames'],'duration':tl['frames']/24,'storyBeats':[x['id'] for x in tl['scenes']]}))

if __name__=='__main__':main()

