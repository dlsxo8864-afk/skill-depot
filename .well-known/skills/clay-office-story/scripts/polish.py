"""Final geometry and lighting corrections after rendering the foundation."""
import math
import bpy

def character(g, fig, spec, col):
    cid=fig['id'];p=fig['proportions'];head=fig['head'];rx,ry,rz=p['head_scale'];z=.85*rz
    hair=fig['materials']['hair'];skin=fig['materials']['skin'];top=fig['materials']['top'];bottom=fig['materials']['bottom']
    # Fill articulated joints with soft clay volumes. The rig remains fully editable.
    for side in ['l','r']:
        g.create_sphere(cid+'_soft_knee_'+side,.067,parent=fig['kn_'+side],material=bottom,collection=col)
        g.create_sphere(cid+'_soft_elbow_'+side,.044,parent=fig['el_'+side],material=top if 'jacket' in spec['outfit']['type'] or 'cardigan' in spec['outfit']['type'] or 'sweater' in spec['outfit']['type'] else skin,collection=col)
        g.create_sphere(cid+'_soft_shoulder_'+side,.054,parent=fig['sh_'+side],material=top,collection=col)
    # Make the eyes and mouth legible at phone size without speaking animation.
    for side in ['L','R']:
        fig['eye_'+side].scale=(1.18,1.0,1.18)
        obj=bpy.data.objects.get(cid+'_blush_'+side)
        if obj: obj.scale*=.60
    for pt in fig['mouth'].data.splines[0].bezier_points:
        pt.co.x*=1.5
    fig['mouth'].location.z=rz*.56
    # Replace tubular locks with overlapping sculpted tufts.
    keep=cid+'_hair_skull'
    for obj in list(col.objects):
        if obj.parent==head and obj.name!=keep and any(tag in obj.name for tag in ['_bob_','_part_','_curl_','_wavy_','_swept_','_ponytail_wisp']):
            bpy.data.objects.remove(obj,do_unlink=True)
    def tuft(label,pos,size,tilt=0):
        o=g.create_sphere(cid+'_sculpt_'+label,1,location=pos,scale=size,material=hair,parent=head,collection=col,segments=32,ring_count=20)
        o.rotation_euler.y=tilt
        return o
    style=spec['hair']['style']
    if style=='bob':
        for sign in [-1,1]:
            tuft('side'+str(sign),(sign*rx*.94,.018,z-.01),(.067,.182,.19),sign*.08)
        tuft('fringe',(-.06,-ry*.67,z+rz*.65),(.19,.052,.065),-.24)
    elif style=='ponytail':
        tuft('swept',(-.05,-ry*.72,z+rz*.63),(.18,.046,.062),-.25)
        tuft('tail',(rx*.5,ry*1.1,z+.015),(.085,.09,.20),-.25)
    elif style=='short_wavy':
        for i in range(5):
            x=(i-2)*.073
            tuft(str(i),(x,-ry*.61,z+rz*.65+.025*math.sin(i)),(.085,.065,.075),(i-2)*.10)
        for sign in [-1,1]:tuft('side'+str(sign),(sign*rx*.92,.0,z+.02),(.055,.13,.13),sign*.25)
    elif style=='curly':
        for row in range(3):
            for i in range(5):
                x=(i-2)*.077;y=-ry*.67+row*.11
                zz=z+rz*.71+.045*row-.018*abs(i-2)
                tuft(f'{row}_{i}',(x,y,zz),(.065,.065,.065))
    else:
        for i in range(4):
            x=(i-1.5)*.09
            tuft(str(i),(x,-ry*.40,z+rz*.78+.02*i),(.087,.145,.066),-.28)
    # Proper collar leaves, buttons, and jacket lapels replace U-shaped collars.
    old=bpy.data.objects.get(cid+'_collar')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    white=g.create_clay_material(cid+'_trim',(.85,.86,.82,1),roughness=.7)
    if 'blouse' in spec['outfit']['type'] or 'shirt' in spec['outfit']['type']:
        for sign in [-1,1]:
            g.create_beveled_box(cid+'_collar_leaf_'+str(sign),(.07,.017,.065),location=(sign*.042,-.126,.29),rotation=(0,sign*.30,0),bevel_width=.008,material=white,parent=fig['hips'],collection=col)
        for i in range(3):g.create_sphere(cid+'_button_'+str(i),.009,location=(0,-.129,.11+i*.065),material=white,parent=fig['hips'],collection=col)
    elif 'jacket' in spec['outfit']['type'] or 'cardigan' in spec['outfit']['type']:
        inner=g.create_clay_material(cid+'_inner',tuple(spec['outfit']['inner_color']),roughness=.7)
        g.create_beveled_box(cid+'_inner_panel',(.12,.012,.27),location=(0,-.128,.18),bevel_width=.015,material=inner,parent=fig['hips'],collection=col)
        for sign in [-1,1]:g.create_beveled_box(cid+'_lapel_'+str(sign),(.065,.018,.18),location=(sign*.07,-.139,.24),rotation=(0,sign*-.22,0),bevel_width=.008,material=top,parent=fig['hips'],collection=col)
    for obj in col.objects:
        if obj.type=='MESH' and any(x in obj.name for x in ['torso','pelvis']):
            for m in obj.modifiers:
                if m.type=='BEVEL':m.width=.065;m.segments=5;m.profile=.5
            mod=obj.modifiers.new('weighted_surface','WEIGHTED_NORMAL');mod.keep_sharp=True
    # Gentle clay grain, no external texture files.
    for mat in fig['materials'].values():
        nodes=mat.node_tree.nodes;bs=nodes.get('Principled BSDF')
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=65
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08;bump.inputs['Distance'].default_value=.008
        mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])

def studio(g,collection):
    mat=g.create_clay_material('warm_backdrop',(.78,.72,.63,1),roughness=.85)
    g.create_beveled_box('studio_background',(12,.1,8),location=(0,3,3),material=mat,collection=collection,bevel_width=.01)
    s=bpy.context.scene
    s.view_settings.view_transform='AgX'
    s.view_settings.look='AgX - Medium High Contrast'
    s.view_settings.exposure=0
