"""A restrained categorical palette and lightness-ordered scientific color maps.

Color-map anchors are interpolated in CIELAB (D65), not directly in sRGB.
The diagnostic is a design screen; it does not certify accessibility.
"""
import numpy as np
from matplotlib import colors

INK='#24324B'
BLUE='#4059A9'
TEAL='#087E83'
RED='#B34567'
GOLD='#AD7E26'
PURPLE='#7868A8'
GREY='#7D8796'
RUST='#B26744'
GRID='#E5EAF1'

_RGB_XYZ=np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]])
_WHITE=np.array([.95047,1.,1.08883])

def rgb_to_lab(rgb):
    rgb=np.asarray(rgb,dtype=float)
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    xyz=(linear@_RGB_XYZ.T)/_WHITE
    d=6/29
    f=np.where(xyz>d**3,np.cbrt(xyz),xyz/(3*d*d)+4/29)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],axis=-1)

def lab_to_rgb(lab):
    lab=np.asarray(lab,dtype=float)
    fy=(lab[...,0]+16)/116
    f=np.stack([fy+lab[...,1]/500,fy,fy-lab[...,2]/200],axis=-1)
    d=6/29
    xyz=np.where(f>d,f**3,3*d*d*(f-4/29))*_WHITE
    linear=xyz@np.linalg.inv(_RGB_XYZ).T
    rgb=np.where(linear<=.0031308,12.92*linear,1.055*np.maximum(linear,0)**(1/2.4)-.055)
    return np.clip(rgb,0,1)

def lab_map(name, anchors, positions=None, n=256):
    a=rgb_to_lab(np.array([colors.to_rgb(c) for c in anchors]))
    p=np.linspace(0,1,len(a)) if positions is None else np.asarray(positions)
    q=np.linspace(0,1,n)
    lab=np.stack([np.interp(q,p,a[:,k]) for k in range(3)],axis=-1)
    return colors.ListedColormap(lab_to_rgb(lab),name=name)

SEQ=lab_map('group_memory_sequential',['#F6F9FB','#B9D8DB','#5AADB1','#127B87','#1A3459'],[0,.24,.50,.74,1])
DIV=lab_map('group_memory_signed',[RED,'#DFA9BB','#F8F8F6','#A2CFD0',TEAL],[0,.25,.5,.75,1],n=257)

def luminance(color):
    c=np.asarray(colors.to_rgb(color));c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    return float(c@np.array([.2126,.7152,.0722]))

def diagnostics():
    seq=rgb_to_lab(SEQ(np.linspace(0,1,256))[:,:3])[:,0]
    div=rgb_to_lab(DIV(np.linspace(0,1,257))[:,:3])[:,0]
    assert np.all(np.diff(seq)<1e-5)
    assert np.all(np.diff(div[:129])>0) and np.all(np.diff(div[128:])<0)
    return dict(categorical={name:dict(hex=c,contrast_on_white=1.05/(luminance(c)+.05)) for name,c in [('ink',INK),('blue',BLUE),('teal',TEAL),('rumor',RED),('gold',GOLD),('purple',PURPLE),('gray',GREY),('thinning',RUST)]},sequential_lightness_monotone=True,diverging_branches_lightness_monotone=True,normalization='Unchanged linear scales; zero center for signed contrasts.',note='Lightness and contrast screening is not a complete color-vision/accessibility assessment. Markers and line styles provide redundant encoding.')
