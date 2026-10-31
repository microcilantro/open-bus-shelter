import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ikea import *

OUT = sys.argv[1]
OLD = 0.6          # line grey for parts already installed
V = (-0.75, 1.0, 0.8)
FULL = ((-8, 128), (-2, 52), (-3, 124))
LOW = ((-4, 124), (-6, 16), (-4, 38))
WF, HF = 1488, 1280      # full-page step image (display 744x640)
WH, HH = 1488, 760       # half-page (display 744x380)


def save(img, name):
    img.save(f"{OUT}/{name}.png", optimize=True); print("wrote", name)


def frame(sc, line=OLD, upto="base"):
    order = ["posts", "base", "arms", "braces", "beams", "purlins", "rail"]
    for xc in POSTS:
        post(sc, xc, line)
        if order.index(upto) >= 1:
            base(sc, xc, line)
    if order.index(upto) >= 2:
        arms(sc, line)
    if order.index(upto) >= 3:
        braces(sc, line)
    if order.index(upto) >= 4:
        beams(sc, line); beam_angles(sc, line)
    if order.index(upto) >= 5:
        purlins(sc, line)
    if order.index(upto) >= 6:
        rail(sc, line)


# ---------- tools as simple solids ----------
def drill(sc, tip, line=0.0, bit=7.0):
    t = np.asarray(tip, float)
    sc.obj(line); sc.cyl(t, t + [0, 0, bit], 0.25, fill=0.95, n=16)
    sc.obj(line); sc.cyl(t + [0, 0, bit], t + [0, 0, bit + 2.2], 0.75, fill=0.9, n=24)
    sc.obj(line); sc.box(t[0] - 1.6, t[0] + 1.6, t[1] - 1.4, t[1] + 1.4, t[2] + bit + 2.2, t[2] + bit + 10, fill=0.96)
    sc.obj(line); sc.box(t[0] - 1.2, t[0] + 1.2, t[1] + 1.4, t[1] + 7.5, t[2] + bit + 6.5, t[2] + bit + 9.5, fill=0.96)


def impact(sc, top, line=0.0):
    t = np.asarray(top, float)
    sc.obj(line); sc.cyl(t + [0, 0, 0.1], t + [0, 0, 1.6], 0.62, fill=0.9, n=24)
    sc.obj(line); sc.cyl(t + [0, 0, 1.6], t + [0, 0, 2.6], 0.4, fill=0.95, n=16)
    sc.obj(line); sc.box(t[0] - 1.5, t[0] + 1.5, t[1] - 1.3, t[1] + 1.3, t[2] + 2.6, t[2] + 9, fill=0.96)
    sc.obj(line); sc.box(t[0] - 1.1, t[0] + 1.1, t[1] + 1.3, t[1] + 6.5, t[2] + 5.8, t[2] + 8.6, fill=0.96)


def level(sc, x, y0, z0, line=0.0):
    sc.obj(line); sc.box(x - 0.8, x + 0.8, y0, y0 + 1.3, z0, z0 + 24, fill=0.97)
    sc.obj(line); sc.box(x - 0.45, x + 0.45, y0 + 1.3, y0 + 1.36, z0 + 11, z0 + 13, fill=0.55)


# ===================================================================== steps
def cover():
    sc = Scene(); slab(sc, -40, 160, 60)
    frame(sc, 0.0, "rail"); panels(sc, 0.25)
    cam = Ortho(V, 1488, 1240)
    img = render(sc, cam, fit_box=((-30, 150), (-16, 60), (-4, 124)))
    save(img, "cover")


def s01():
    sc = Scene(); slab(sc, -24, 144, 60)
    cam = Ortho((-0.2, 0.75, 1.5), WH, HH, margin=0.12)
    img = render(sc, cam); a = Ann(img, cam)
    a.mark((12, 6, 0)); a.mark((108, 6, 0))
    a.dim((12, 6, 0), (108, 6, 0), "2438 mm / 8'-0\"", off=(0, 54))
    a.dim((108, 0, 0), (108, 6, 0), "152 / 6\"", off=(-70, 0))
    a.dim((12, 0, 0), (12, 6, 0), "152 / 6\"", off=(70, 0))
    save(img, "s01")


def d02():
    """bolt through two backs, nut inside second channel"""
    sc = Scene()
    strut(sc, [[0, 6], [-S, 0], [0, S]], 1, -1, OLD)
    strut(sc, [[0, 6], [0, S], [0, S]], 1, +1, OLD)
    bolt(sc, (3, -S + 0.11, S / 2), (0, 1, 0), length=2.6)
    sc.obj(0.0); sc.cyl((3, S - 0.11, S / 2), (3, S - 0.21, S / 2), 0.69, fill=0.95, n=36)
    sc.obj(0.0); sc.hexp((3, S - 0.21, S / 2), (3, S - 0.65, S / 2), 0.75, fill=0.92)
    cam = Ortho((0.55, -1.0, 0.55), 900, 900, margin=0.06)
    return render(sc, cam, fit_box=((0.5, 5.5), (-2.4, 2.0), (-0.3, 2.0)), sil_px=9, cre_px=3)


def s02():
    sc = Scene()
    strut(sc, [[0, 120], [-S, 0], [0, S]], 1, -1, 0.0)
    strut(sc, [[0, 120], [7, 7 + S], [0, S]], 1, +1, 0.0)
    for xb in (6, 54, 114):
        bolt(sc, (xb, -3.4, S / 2), (0, 1, 0), length=1.25)
    cam = Ortho((-0.55, 1.0, 1.0), WH, HH, margin=0.1)
    img = render(sc, cam, fit_box=((0, 120), (-4, 9), (0, S)))
    a = Ann(img, cam)
    a.arrow((60, 11.5, S / 2), (60, 8.2, S / 2))
    a.tag((110, 7.8, S), "A", "×2", off=(40, -60))
    a.tag((54, -3.6, S / 2), "G+H", "×6", off=(-80, 60))
    a.big((680, 50), "×2")
    det = d02()
    bubble(img, det, (125, 250), 105, target=tuple(np.array(a.P((6, 0, S / 2))) / 2))
    save(img, "s02")


def s03():
    sc = Scene()
    post(sc, 0, line=OLD, h=10)
    angle_fitting(sc, 0, 7.625 + 6, 0, +1, 0.0)
    angle_fitting(sc, 0, 4.375 - 6, 0, -1, 0.0)
    for z in (1.1, 2.9):
        bolt(sc, (0, 7.625 + 6 + 0.25 + 3.5, z), (0, -1, 0), length=1.25)
        spring_nut(sc, (0, 7.2, z), (0, 1, 0), (0, 0, 1))
    cam = Ortho((-0.95, 1.0, 0.7), WH, HH, margin=0.08)
    img = render(sc, cam, fit_box=((-2, 2), (-6, 22), (-0.5, 8)))
    a = Ann(img, cam)
    a.arrow((0, 13.4, 1.8), (0, 9.4, 1.8)); a.arrow((0, -1.4, 1.8), (0, 2.6, 1.8))
    a.tag((0, 16.5, 0.2), "E", "×2", off=(70, 40))
    a.tag((0, 17.6, 2.9), "G+H", "×4", off=(60, -80))
    a.tag((0, 7.4, 2.9), "F", "×4", off=(-170, -60))
    a.big((690, 40), "×2")
    save(img, "s03")


def d04():
    sc = Scene()
    sc.obj(0.45); sc.box(-5, 5, 4.5, 14, -4, 0)
    angle_fitting(sc, 0, 7.625, 0, +1, OLD)
    drill(sc, (0, 8.725, -1.5), 0.0, bit=6)
    cam = Ortho((-0.9, 1.0, 0.75), 900, 900, margin=0.04)
    return render(sc, cam, fit_box=((-5, 5), (5, 13), (-4, 8)), sil_px=9)


def s04():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "base")
    level(sc, 12, 7.625 + 0.3, 6)
    drill(sc, (108, 8.725, 2.5), 0.0, bit=7)
    cam = Ortho(V, WF, HF, margin=0.05)
    img = render(sc, cam, fit_box=LOW); a = Ann(img, cam)
    a.dim((12, 32, 0), (108, 32, 0), "2438 mm / 8'-0\"", ext=False)
    a.big((660, 60), "×8")
    bubble(img, d04(), (560, 470), 150, target=tuple(np.array(a.P((108, 8.7, 0.3))) / 2))
    save(img, "s04")


def d05():
    sc = Scene()
    sc.obj(0.45); sc.box(-5, 5, 4.5, 14, -4, 0)
    angle_fitting(sc, 0, 7.625, 0, +1, OLD)
    anchor(sc, (0, 10.525, 0.25), 4.0, OLD)
    anchor(sc, (0, 8.725, 0.25 + 5.5), 4.0, 0.0)
    impact(sc, (0, 8.725, 0.25 + 5.5 + 0.33), 0.0)
    cam = Ortho((-0.9, 1.0, 0.75), 900, 900, margin=0.04)
    img = render(sc, cam, fit_box=((-5, 5), (5, 13), (-4, 16)), sil_px=9)
    return img, cam


def s05():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "base")
    for xc in POSTS:
        for (x, y) in HOLES(xc):
            anchor(sc, (x, y, 11), 4.0, 0.0)
    cam = Ortho(V, WF, HF, margin=0.05)
    img = render(sc, cam, fit_box=LOW); a = Ann(img, cam)
    a.tag((108, 10.5, 11.4), "J", "×8", off=(-90, -60))
    bubble(img, d05()[0], (560, 470), 150, target=tuple(np.array(a.P((12, 8.7, 0.3))) / 2))
    save(img, "s05")


def d06():
    sc = Scene()
    xc = 12; sg = 1; ax = arm_x(xc); zt = u(ax)
    post(sc, xc, OLD, h=10, z0=zt - 6)
    strut(sc, [[ax - S / 2, ax + S / 2], [-2, 14], [zt - S, zt]], 0, -sg, 0.0)
    post_angles(sc, xc, 0.0)
    cam = Ortho((-0.9, 1.0, 0.75), 900, 900, margin=0.05)
    return render(sc, cam, fit_box=((8, 18), (-1, 13), (zt - 5, zt + 3)), sil_px=9)


def s06():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "base"); arms(sc, 0.0)
    cam = Ortho(V, WF, HF)
    img = render(sc, cam, fit_box=FULL); a = Ann(img, cam)
    z1, z2 = u(arm_x(12)), u(arm_x(108))
    a.dim((12, 0, 0), (12, 0, z1), "2616 / 8'-7\"", off=(70, 0))
    a.dim((108, 0, 0), (108, 0, z2), "2819 / 9'-3\"", off=(-70, 0))
    a.tag((arm_x(108), 36, z2), "B", "×2", off=(-40, -70))
    bubble(img, d06(), (590, 120), 110, target=tuple(np.array(a.P((12, 7.7, z1 - 0.8))) / 2))
    save(img, "s06")


def s07():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "arms"); braces(sc, 0.0)
    cam = Ortho(V, WF, HF)
    img = render(sc, cam, fit_box=FULL); a = Ann(img, cam)
    ax = arm_x(108); zt = u(ax)
    a.tag((ax, 16, zt - S - 8.5), "C", "×2", off=(-110, 30))
    save(img, "s07")


def d08():
    sc = Scene()
    xc = 12; sg = 1; ax = arm_x(xc); zt = u(ax)
    strut(sc, [[ax - S / 2, ax + S / 2], [-4, 8], [zt - S, zt]], 0, -sg, OLD)
    sc.obj(OLD); sc.sloped(ax - 8, ax + 8, 0, S, u, S)
    xl = ax - sg * S / 2
    sc.obj(0.0); sc.box(xl - 0.25, xl, 0, S, zt - 3.0, zt)
    sc.obj(0.0); sc.box(xl - 3.0, xl - 0.25, 0, S, zt - 0.25, zt)
    bolt(sc, (xl - 1.6, S / 2, u(xl - 1.6) + S + 3.0), (0, 0, -1), length=1.25)
    cam = Ortho((-0.9, 1.0, 0.75), 900, 900, margin=0.05)
    return render(sc, cam, fit_box=((ax - 7, ax + 4), (-3, 6), (zt - 4, zt + 6)), sil_px=9)


def s08():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "braces")
    beams(sc, 0.0, dz=12); beam_angles(sc, 0.0)
    cam = Ortho(V, WF, HF)
    img = render(sc, cam, fit_box=FULL); a = Ann(img, cam)
    for x in POSTS:
        for y in (0.8, 47.2):
            ax = arm_x(x)
            a.arrow((ax, y, u(ax) + 11), (ax, y, u(ax) + 3), width=5, head=16)
    a.tag((60, 47.2, u(60) + 13.6), "A", "×2", off=(30, 60))
    a.tag((arm_x(12), 47, u(arm_x(12)) - 1), "E", "×4", off=(60, 60))
    bubble(img, d08(), (110, 120), 100, target=tuple(np.array(a.P((arm_x(108) + 1, 0.8, u(arm_x(108))))) / 2))
    save(img, "s08")


def s09():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "beams"); purlins(sc, 0.0)
    cam = Ortho(V, WF, HF)
    img = render(sc, cam, fit_box=FULL); a = Ann(img, cam)
    zz = lambda x: u(x) + 2 * S + 0.5
    xs = [0, 36, 60, 84, 120]
    labels = ["914 / 3'", "610 / 2'", "610 / 2'", "914 / 3'"]
    for i in range(4):
        a.dim((xs[i], 48, zz(xs[i])), (xs[i + 1], 48, zz(xs[i + 1])), labels[i], off=(18, 34))
    a.tag((60, 24, u(60) + 2 * S), "B", "×5", off=(30, -110))
    save(img, "s09")


def s10():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "purlins"); rail(sc, 0.0)
    cam = Ortho(V, WF, HF)
    img = render(sc, cam, fit_box=FULL); a = Ann(img, cam)
    a.dim((118, 9.25, 0), (118, 9.25, 32), "813 / 2'-8\"", off=(-30, 0))
    a.tag((60, 9.25, 31.2), "A", "×1", off=(20, 80))
    a.tag((12, 7.7, 31.2), "G+F", "×4", off=(70, -70))
    save(img, "s10")


def d11():
    sc = Scene()
    strut(sc, [[-1, 1 + S], [-6, 6], [0, S]], 2, +1, OLD)
    sc.obj(0.0)
    import math
    n = 48; xs = np.linspace(-1.5, 3.5, 2)
    # corrugated sheet across the purlin: corrugations run along x
    ys = np.linspace(-6, 6, 97)
    zs = S + 0.42 + 0.42 * np.cos(ys / 2.67 * 2 * np.pi)
    for i in range(len(ys) - 1):
        sc.face([(-1.5, ys[i], zs[i]), (3.5, ys[i], zs[i]), (3.5, ys[i + 1], zs[i + 1]), (-1.5, ys[i + 1], zs[i + 1])], fill=0.97, kind=0,
                normal=np.array([0, -(zs[i + 1] - zs[i]), ys[i + 1] - ys[i]]) / np.hypot(zs[i + 1] - zs[i], ys[i + 1] - ys[i]))
    yc = 0.0; ztop = S + 0.84
    sc.obj(0.0); sc.hexp((0.8, yc, ztop + 1.6), (0.8, yc, ztop + 1.95), 0.31, fill=0.9)
    sc.obj(0.0); sc.cyl((0.8, yc, ztop + 1.5), (0.8, yc, ztop + 1.6), 0.32, fill=0.6, n=24)
    sc.obj(0.0); sc.cyl((0.8, yc, ztop - 0.2), (0.8, yc, ztop + 1.5), 0.095, fill=0.98, n=12)
    cam = Ortho((-0.8, 1.0, 0.65), 900, 900, margin=0.05)
    return render(sc, cam, fit_box=((-1.5, 3.5), (-5, 5), (0, 4.5)), sil_px=9, cre_px=3)


def s11():
    sc = Scene(); slab(sc, -24, 144, 60)
    frame(sc, OLD, "rail"); panels(sc, 0.0, dz=14, split=True)
    cam = Ortho(V, WF, HF)
    img = render(sc, cam, fit_box=((-14, 134), (-2, 52), (-3, 140))); a = Ann(img, cam)
    a.arrow((60, 36, u(60) + 2 * S + 13), (60, 36, u(60) + 2 * S + 3))
    a.tag((112, 40, u(112) + 2 * S + 14), "D", "×2", off=(40, -50))
    a.tag((0, 12, u(0) + 2 * S), "K", "×60", off=(-60, 70))
    bubble(img, d11(), (110, 470), 100, target=tuple(np.array(a.P((0, 12, u(0) + 2 * S))) / 2))
    save(img, "s11")


def bench_step(stage):
    sc = Scene(); slab(sc, -10, 140, 84, back=True)
    for xc in POSTS:
        post(sc, xc, OLD); base(sc, xc, OLD)
    rail(sc, OLD)
    bench(sc, stage, 0.0, OLD)
    cam = Ortho((0.9, 1.0, 0.65), WH, HH, margin=0.06)
    img = render(sc, cam, fit_box=((14, 80), (0, 34), (0, 42))); a = Ann(img, cam)
    if stage == 1:
        a.tag((40, 9.25, 15.7), "A", "×1", off=(-60, 60))
        a.tag((46, 25, 18.1), "C", "×5", off=(60, -60))
    if stage == 2:
        a.tag((22, 20, 25.6), "C", "×4", off=(-70, -50))
    if stage == 3:
        a.tag((46, 20, 19.1), "N", "×5", off=(60, -80))
        a.dim((20, 34, 19.1), (72, 34, 19.1), "1320 / 52\"", off=(0, 34))
    save(img, f"b{stage}")


ALL = dict(cover=cover, s01=s01, s02=s02, s03=s03, s04=s04, s05=s05, s06=s06, s07=s07, s08=s08, s09=s09,
           s10=s10, s11=s11, b1=lambda: bench_step(1), b2=lambda: bench_step(2), b3=lambda: bench_step(3))

if __name__ == "__main__":
    for n in sys.argv[2:]:
        ALL[n]()
