"""IKEA-style technical line-art renderer (orthographic, hidden-line, two line weights).

Units: inches. x along curb, y toward street, z up.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
INK = (20, 20, 22)
BLUE = (31, 95, 174)
S = 1.625


# ---------------------------------------------------------------- scene ----
class Scene:
    def __init__(self):
        self.tris = []          # (v0, v1, v2, face)
        self.face_obj = []; self.face_n = []; self.face_fill = []; self.face_kind = []
        self.obj_line = []      # line gray per object (0=black)
        self.cur = None

    def obj(self, line=0.0):
        self.obj_line.append(line); self.cur = len(self.obj_line) - 1
        return self.cur

    def face(self, pts, fill=1.0, kind=0, normal=None):
        q = [np.asarray(p, float) for p in pts]
        if normal is None:
            n = np.cross(q[1] - q[0], q[2] - q[0]); n /= (np.linalg.norm(n) + 1e-12)
        else:
            n = np.asarray(normal, float)
        fid = len(self.face_obj)
        self.face_obj.append(self.cur); self.face_n.append(n); self.face_fill.append(fill); self.face_kind.append(kind)
        for i in range(1, len(q) - 1):
            self.tris.append((q[0], q[i], q[i + 1], fid))

    def prism(self, v, fill=1.0, kind=0):
        v = [np.asarray(p, float) for p in v]
        c = sum(v) / 8
        for f in [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            q = [v[i] for i in f]
            n = np.cross(q[1] - q[0], q[2] - q[0]); n /= (np.linalg.norm(n) + 1e-12)
            if np.dot(n, sum(q) / 4 - c) < 0:
                q = q[::-1]; n = -n
            self.face(q, fill, kind, n)

    def box(self, x0, x1, y0, y1, z0, z1, fill=1.0, kind=0):
        self.prism([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], fill, kind)

    def sloped(self, x0, x1, y0, y1, zfn, t, fill=1.0, kind=0):
        a, b = zfn(x0), zfn(x1)
        self.prism([(x0, y0, a), (x1, y0, b), (x1, y1, b), (x0, y1, a),
                    (x0, y0, a + t), (x1, y0, b + t), (x1, y1, b + t), (x0, y1, a + t)], fill, kind)

    def ngon(self, p0, p1, r, n, fill=1.0, phase=0.0, kind=0):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        ax = p1 - p0; L = np.linalg.norm(ax); ax /= L
        a = np.cross(ax, [0, 0, 1.0])
        if np.linalg.norm(a) < 1e-6:
            a = np.cross(ax, [1.0, 0, 0])
        a /= np.linalg.norm(a); b = np.cross(ax, a)
        ang = phase + np.arange(n) * 2 * np.pi / n
        ring0 = [p0 + r * (np.cos(t) * a + np.sin(t) * b) for t in ang]
        ring1 = [p + ax * L for p in ring0]
        self.face(ring0[::-1], fill, kind, -ax)
        self.face(ring1, fill, kind, ax)
        for i in range(n):
            j = (i + 1) % n
            mid = (ang[i] + ang[j]) / 2 if j else (ang[i] + ang[i] + 2 * np.pi / n) / 2
            nrm = np.cos(mid) * a + np.sin(mid) * b
            self.face([ring0[i], ring0[j], ring1[j], ring1[i]], fill, kind, nrm)

    def cyl(self, p0, p1, r, fill=1.0, n=28, kind=0):
        self.ngon(p0, p1, r, n, fill, kind=kind)

    def hexp(self, p0, p1, flats, fill=1.0):
        self.ngon(p0, p1, flats / np.sqrt(3), 6, fill, phase=np.pi / 6)

    def between(self, p0, p1, w, t, fill=1.0):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        a = np.array([1.0, 0, 0]); b = np.cross(d, a); b /= np.linalg.norm(b)
        ha, hb = a * w / 2, b * t / 2
        self.prism([p0 - ha - hb, p0 + ha - hb, p0 + ha + hb, p0 - ha + hb,
                    p1 - ha - hb, p1 + ha - hb, p1 + ha + hb, p1 - ha + hb], fill)


# --------------------------------------------------------------- parts -----
def strut(sc, r, o, sign, line=0.0, slots=True, t=0.105, lip=0.42):
    """C-channel as one object. r=[[x0,x1],[y0,y1],[z0,z1]]; opens toward sign*o."""
    sc.obj(line)
    ext = [r[i][1] - r[i][0] for i in range(3)]
    others = [i for i in range(3) if i != o]
    L = max(others, key=lambda i: ext[i]); w = [i for i in others if i != L][0]

    def add(rr, fill=1.0):
        sc.box(rr[0][0], rr[0][1], rr[1][0], rr[1][1], rr[2][0], rr[2][1], fill)
    lo, hi = r[o]
    b = [list(x) for x in r]; b[o] = [lo, lo + t] if sign > 0 else [hi - t, hi]; add(b)
    for wr in ([r[w][0], r[w][0] + t], [r[w][1] - t, r[w][1]]):
        s = [list(x) for x in r]; s[w] = wr; add(s)
    for wr in ([r[w][0], r[w][0] + lip], [r[w][1] - lip, r[w][1]]):
        s = [list(x) for x in r]; s[w] = wr; s[o] = [hi - t, hi] if sign > 0 else [lo, lo + t]; add(s)
    if slots:
        # half-slot holes on the back, 9/16 x 1-1/8 on 2" centres (drawn as dark recesses)
        wc = (r[w][0] + r[w][1]) / 2
        outer = lo if sign > 0 else hi
        d = -0.03 if sign > 0 else 0.03
        pos = np.arange(r[L][0] + 1.0, r[L][1] - 0.6, 2.0)
        for p in pos:
            s = [None, None, None]
            s[L] = [p - 0.56, p + 0.56]; s[w] = [wc - 0.28, wc + 0.28]
            s[o] = sorted([outer, outer + d])
            add(s, fill=0.30)


def angle_fitting(sc, x, y_face, z0, outward, line=0.0, leg=3.5, w=S, t=0.25):
    """90 deg 4-hole angle: vertical leg against a post face at y=y_face, horizontal leg on z0 pointing outward (+1/-1 in y)."""
    sc.obj(line)
    if outward > 0:
        sc.box(x - w / 2, x + w / 2, y_face, y_face + t, z0, z0 + leg)
        sc.box(x - w / 2, x + w / 2, y_face, y_face + leg, z0, z0 + t)
        holes_v = [(y_face + t + 0.02, z0 + 1.1), (y_face + t + 0.02, z0 + 2.9)]
        holes_h = [y_face + 1.1, y_face + 2.9]
    else:
        sc.box(x - w / 2, x + w / 2, y_face - t, y_face, z0, z0 + leg)
        sc.box(x - w / 2, x + w / 2, y_face - leg, y_face, z0, z0 + t)
        holes_v = [(y_face - t - 0.02, z0 + 1.1), (y_face - t - 0.02, z0 + 2.9)]
        holes_h = [y_face - 1.1, y_face - 2.9]
    for yh in holes_h:
        sc.cyl((x, yh, z0 + t - 0.01), (x, yh, z0 + t + 0.02), 0.28, fill=0.30, n=16)
    return holes_h


def bolt(sc, p, axis, length=1.25, line=0.0, washer=True):
    """Hex bolt; p = underside of head; axis = unit vector of shank direction."""
    p = np.asarray(p, float); ax = np.asarray(axis, float); ax /= np.linalg.norm(ax)
    sc.obj(line)
    sc.hexp(p - ax * 0.31, p, 0.75, fill=0.92)
    sc.cyl(p, p + ax * length, 0.25, fill=0.98, n=20)
    if washer:
        sc.obj(line)
        sc.cyl(p, p + ax * 0.1, 0.69, fill=0.95, n=36)


def spring_nut(sc, center, normal, along, line=0.0):
    c = np.asarray(center, float); n = np.asarray(normal, float); a = np.asarray(along, float)
    b = np.cross(n, a)
    sc.obj(line)
    hl, hw, ht = 0.65, 0.44, 0.19
    pts = []
    for dz in (-ht, ht):
        for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            pts.append(c + n * dz + a * sa * hl + b * sb * hw)
    sc.prism(pts, fill=0.85)


def anchor(sc, top, length=4.0, line=0.0):
    t = np.asarray(top, float)
    sc.obj(line)
    sc.hexp(t + [0, 0, 0.33], t + [0, 0, 0.0], 0.75, fill=0.92)
    sc.cyl(t, t + [0, 0, 0.06], 0.6, fill=0.95, n=32)
    sc.cyl(t, t - [0, 0, length], 0.25, fill=0.98, n=20)


# ------------------------------------------------------------- shelter -----
def u(x):  # top of arms; beams sit here
    return 102 + 10 * x / 120


POSTS = (12, 108)


def arm_x(xc):
    return xc + S + 0.25 if xc < 60 else xc - S - 0.25


def side(xc):
    return 1 if xc < 60 else -1


def post(sc, xc, line=0.0, h=123.5, z0=0.0):
    strut(sc, [[xc - S / 2, xc + S / 2], [6, 7.625], [z0, z0 + h]], 1, +1, line, slots=False)
    strut(sc, [[xc - S / 2, xc + S / 2], [4.375, 6], [z0, z0 + h]], 1, -1, line, slots=False)


def base(sc, xc, line=0.0, explode=0.0):
    angle_fitting(sc, xc, 7.625 + explode, 0, +1, line)
    angle_fitting(sc, xc, 4.375 - explode, 0, -1, line)


HOLES = lambda xc: [(xc, y) for y in (8.725, 10.525, 1.475, 3.275)]


def arms(sc, line=0.0, fittings=True):
    """Arms beside the posts, open toward the post; joined by angle fittings on the post's open faces."""
    for xc in POSTS:
        sg = side(xc); ax = arm_x(xc); zt = u(ax)
        strut(sc, [[ax - S / 2, ax + S / 2], [0, 48], [zt - S, zt]], 0, -sg, line)
        if fittings:
            post_angles(sc, xc, line)


def post_angles(sc, xc, line=0.0):
    sg = side(xc); ax = arm_x(xc); zt = u(ax)
    xp = xc + sg * S / 2           # post inner side
    for yf, o in ((7.625, +1), (4.375, -1)):
        sc.obj(line)
        xa0, xa1 = sorted([xc - sg * S / 2, xp])
        xb0, xb1 = sorted([xp, xp + sg * 0.25])
        if o > 0:
            sc.box(xa0, xa1, yf, yf + 0.25, zt - S, zt)
            sc.box(xb0, xb1, yf, yf + 3.25, zt - S, zt)
        else:
            sc.box(xa0, xa1, yf - 0.25, yf, zt - S, zt)
            sc.box(xb0, xb1, yf - 2.25, yf, zt - S, zt)


def beam_angles(sc, line=0.0):
    for xc in POSTS:
        sg = side(xc); ax = arm_x(xc); zt = u(ax)
        xl = ax - sg * S / 2          # arm open face (toward post)
        for yc in (S / 2, 48 - S / 2):
            sc.obj(line)
            x0, x1 = sorted([xl, xl - sg * 0.25])
            sc.box(x0, x1, yc - S / 2, yc + S / 2, zt - 3.0, zt)
            x0, x1 = sorted([xl - sg * 0.25, xl - sg * 3.0])
            sc.box(x0, x1, yc - S / 2, yc + S / 2, zt - 0.25, zt)


def braces(sc, line=0.0):
    for xc in POSTS:
        ax = arm_x(xc); zt = u(ax)
        sc.obj(line)
        sc.between((ax, 7.625, zt - S - 17), (ax, 7.625 + 17, zt - S), S, S)


def beams(sc, line=0.0, dz=0.0):
    for y0 in (0, 48 - S):
        sc.obj(line)
        sc.sloped(0, 120, y0, y0 + S, lambda x: u(x) + dz, S)


PURL = (0, 36 - S / 2, 60 - S / 2, 84 - S / 2, 120 - S)


def purlins(sc, line=0.0, dz=0.0):
    for xp in PURL:
        z0 = u(xp + S / 2) + S + dz
        strut(sc, [[xp, xp + S], [0, 48], [z0, z0 + S]], 2, +1, line, slots=False)


def rail(sc, line=0.0, z0=30.4):
    strut(sc, [[0, 120], [7.625, 9.25], [z0, z0 + S]], 1, +1, line)


def panels(sc, line=0.35, dz=0.0, split=False):
    sc.obj(line)
    if split:
        sc.sloped(-12, 132, -1, 25, lambda x: u(x) + 2 * S, 0.35, fill=1.0, kind=1)
        sc.obj(line)
        sc.sloped(-12, 132, 22.5, 49.5, lambda x: u(x) + 2 * S + dz, 0.35, fill=1.0, kind=1)
    else:
        sc.sloped(-12, 132, -1, 49.5, lambda x: u(x) + 2 * S, 0.35, fill=1.0, kind=1)


def slab(sc, x0=-30, x1=150, y1=60, line=0.45, back=True):
    sc.obj(line); sc.box(x0, x1, 0, y1, -4, 0, fill=1.0)
    if back:
        sc.obj(line); sc.box(x0, x1, -16, 0, -4, 3, fill=0.97)


def bench(sc, stage, new=0.0, old=0.55):
    l1 = new if stage == 1 else old
    l2 = new if stage == 2 else old
    l3 = new if stage == 3 else old
    strut(sc, [[0, 120], [7.625, 9.25], [14.875, 16.5]], 1, -1, l1)
    for xa in (22, 46, 70):
        strut(sc, [[xa - S / 2, xa + S / 2], [7.625, 31.625], [16.5, 18.125]], 2, +1, l1)
    for xa in (22, 70):
        strut(sc, [[xa - S / 2, xa + S / 2], [30, 31.625], [0, 24]], 1, +1, l1)
    if stage >= 2:
        for xa in (22, 70):
            strut(sc, [[xa - S / 2, xa + S / 2], [9.25, 31.625], [24, 25.625]], 2, -1, l2)
            strut(sc, [[xa - S / 2, xa + S / 2], [9.25, 10.875], [16.5, 40.5]], 1, +1, l2)
    if stage >= 3:
        for y0 in (12, 18, 24):
            sc.obj(l3); sc.box(20, 72, y0, y0 + 5.5, 18.125, 19.125, fill=0.96)
        for z0 in (24, 30.5):
            sc.obj(l3); sc.box(20, 72, 10.875, 11.875, z0, z0 + 5.5, fill=0.96)


# ------------------------------------------------------------ renderer -----
class Ortho:
    def __init__(self, view_dir, W, H, ss=2, margin=0.07, up=(0, 0, 1)):
        f = -np.asarray(view_dir, float); f /= np.linalg.norm(f)   # looking direction
        r = np.cross(f, up); r /= np.linalg.norm(r)
        d = np.cross(f, r)
        self.R = np.stack([r, d, f]); self.W, self.H, self.ss, self.margin = W, H, ss, margin
        self.k = 1.0; self.ox = 0.0; self.oy = 0.0

    def fit(self, pts):
        c = np.asarray(pts, float) @ self.R.T
        W2, H2 = self.W * self.ss, self.H * self.ss; m = self.margin
        self.k = min(W2 * (1 - 2 * m) / np.ptp(c[:, 0]), H2 * (1 - 2 * m) / np.ptp(c[:, 1]))
        self.ox = W2 / 2 - self.k * (c[:, 0].max() + c[:, 0].min()) / 2
        self.oy = H2 / 2 - self.k * (c[:, 1].max() + c[:, 1].min()) / 2

    def screen(self, P):
        c = np.asarray(P, float) @ self.R.T
        out = np.empty_like(c)
        out[..., 0] = self.ox + self.k * c[..., 0]; out[..., 1] = self.oy + self.k * c[..., 1]; out[..., 2] = c[..., 2]
        return out

    def P(self, p):  # final-image pixel coords
        s = self.screen(np.asarray(p, float))
        return (s[0] / self.ss, s[1] / self.ss)


def raster(T, ids, W, H):
    zb = np.full((H, W), np.inf); ib = np.full((H, W), -1, np.int64)
    for k in range(len(T)):
        p = T[k]
        x0 = max(int(np.floor(p[:, 0].min())), 0); x1 = min(int(np.ceil(p[:, 0].max())), W - 1)
        y0 = max(int(np.floor(p[:, 1].min())), 0); y1 = min(int(np.ceil(p[:, 1].max())), H - 1)
        if x0 > x1 or y0 > y1:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = p
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
        w1 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-7) & (w1 >= -1e-7) & (w2 >= -1e-7)
        if not m.any():
            continue
        z = w0 * az + w1 * bz + w2 * cz
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = m & (z < sub)
        sub[upd] = z[upd]; ib[y0:y1 + 1, x0:x1 + 1][upd] = ids[k]
    return zb, ib


def _edges(ib, zb, fobj, fn, oline, crease=0.75, zjump=0.6):
    H, W = ib.shape
    hit = ib >= 0
    idx = np.where(hit, ib, 0)
    obj = np.where(hit, fobj[idx], -1)
    nn = fn[idx]
    lg = np.where(hit, oline[np.where(hit, obj, 0)], 1.0)
    sil = np.ones((H, W)); cre = np.ones((H, W))
    for sl_a, sl_b in (((slice(None), slice(None, -1)), (slice(None), slice(1, None))),
                       ((slice(None, -1), slice(None)), (slice(1, None), slice(None)))):
        oa, ob = obj[sl_a], obj[sl_b]
        za, zb2 = zb[sl_a], zb[sl_b]
        diff_obj = oa != ob
        with np.errstate(invalid='ignore'):
            samejump = (~diff_obj) & (oa >= 0) & (np.abs(za - zb2) > zjump)
        s_edge = diff_obj | samejump
        dot = np.sum(nn[sl_a] * nn[sl_b], axis=-1)
        c_edge = (~s_edge) & (oa >= 0) & (dot < crease)
        val = np.minimum(lg[sl_a], lg[sl_b])
        # silhouette colour: the nearer object's line colour
        near_a = za <= zb2
        sval = np.where(diff_obj, np.where(near_a, lg[sl_a], lg[sl_b]), val)
        sval = np.where((oa < 0), lg[sl_b], np.where(ob < 0, lg[sl_a], sval))
        tgt = sil[sl_a]; np.minimum(tgt, np.where(s_edge, sval, 1.0), out=tgt)
        tgt = cre[sl_a]; np.minimum(tgt, np.where(c_edge, val, 1.0), out=tgt)
    return sil, cre


def render(sc, cam, fit_box=None, L=(-0.45, 0.35, 0.82), sil_px=7, cre_px=3, panel_tint=(0.88, 0.92, 0.97)):
    T = np.array([[t[0], t[1], t[2]] for t in sc.tris]); fid = np.array([t[3] for t in sc.tris])
    fobj = np.array(sc.face_obj); fn = np.array(sc.face_n); ffill = np.array(sc.face_fill)
    fkind = np.array(sc.face_kind); oline = np.array(sc.obj_line, float)
    if fit_box is not None:
        (x0, x1), (y0, y1), (z0, z1) = fit_box
        cam.fit(np.array([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]))
    else:
        cam.fit(T.reshape(-1, 3))
    Sx = cam.screen(T)
    W2, H2 = cam.W * cam.ss, cam.H * cam.ss
    opaque = fkind[fid] == 0
    zb, ib = raster(Sx[opaque], fid[opaque], W2, H2)
    Lv = np.array(L, float); Lv /= np.linalg.norm(Lv)
    hit = ib >= 0; idx = np.where(hit, ib, 0)
    shade = 0.87 + 0.13 * np.clip(fn[idx] @ Lv, 0, 1)
    fill = np.where(hit, ffill[idx] * shade, 1.0)
    sil, cre = _edges(ib, zb, fobj, fn, oline)
    sil = np.array(Image.fromarray((sil * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(sil_px))) / 255
    cre = np.array(Image.fromarray((cre * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(cre_px))) / 255
    img = np.minimum(np.minimum(fill, sil), cre)
    rgb = np.repeat(img[..., None], 3, axis=2)
    if (~opaque).any():
        zp, ip = raster(Sx[~opaque], fid[~opaque], W2, H2)
        ph = (ip >= 0) & (zp < zb)
        rgb = np.where(ph[..., None], rgb * 0.55 + np.array(panel_tint) * 0.45, rgb)
        psil, pcre = _edges(np.where(ph, ip, -1), zp, fobj, fn, oline)
        psil = np.array(Image.fromarray((psil * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) / 255
        rgb = np.minimum(rgb, psil[..., None])
        # corrugation hint: thin lines along x on the panel
        if ph.any():
            jj, ii = np.meshgrid(np.arange(W2), np.arange(H2))
    out = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((cam.W, cam.H), Image.LANCZOS)
    return out


# ---------------------------------------------------------- annotation -----
class Ann:
    def __init__(self, img, cam, scale=2.0):
        self.img, self.cam, self.s = img, cam, scale
        self.d = ImageDraw.Draw(img)
        self.fb = ImageFont.truetype(FONT_B, int(22 * scale))
        self.fs = ImageFont.truetype(FONT_B, int(16 * scale))
        self.fm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", int(15 * scale))

    def P(self, p):
        return np.array(self.cam.P(p))

    def arrow(self, a, b, width=7, head=22, screen=False):
        s = self.s
        a = np.asarray(a if screen else self.P(a), float); b = np.asarray(b if screen else self.P(b), float)
        d = b - a; n = np.linalg.norm(d)
        if n < 1:
            return
        d /= n; p = np.array([-d[1], d[0]])
        w, hl, hw = width * s / 2, head * s, head * s * 0.62
        base = b - d * hl
        poly = [a + p * w, base + p * w, base + p * hw, b, base - p * hw, base - p * w, a - p * w]
        self.d.polygon([tuple(q) for q in poly], fill="white", outline=INK, width=int(2.4 * s))

    def curl(self, c, r=26, start=200, end=500, screen=False):
        """Curved rotate arrow around point c (screen)."""
        s = self.s
        c = np.asarray(c if screen else self.P(c), float); r = r * s
        ts = np.radians(np.linspace(start, end - 30, 30))
        pts = [tuple(c + r * np.array([np.cos(t), np.sin(t) * 0.55])) for t in ts]
        self.d.line(pts, fill=INK, width=int(3 * s), joint="curve")
        te = np.radians(end - 30); tip = c + r * np.array([np.cos(np.radians(end)), np.sin(np.radians(end)) * 0.55])
        last = np.array(pts[-1]); d = tip - last; d /= np.linalg.norm(d); p = np.array([-d[1], d[0]])
        self.d.polygon([tuple(tip), tuple(last - d * 2 + p * 9 * s), tuple(last - d * 2 - p * 9 * s)], fill=INK)

    def tag(self, p, letter, qty=None, off=(60, -60), screen=False, leader=True):
        s = self.s
        a = np.asarray(p if screen else self.P(p), float); c = a + np.array(off) * s
        if leader:
            self.d.line([tuple(a), tuple(c)], fill=INK, width=int(1.6 * s))
        r = 19 * s
        tw = self.d.textlength(letter, font=self.fb); half = max(r, tw / 2 + 12 * s)
        self.d.rounded_rectangle([c[0] - half, c[1] - r, c[0] + half, c[1] + r], radius=r, fill="white", outline=INK, width=int(2.6 * s))
        self.d.text(tuple(c), letter, font=self.fb, fill=INK, anchor="mm")
        if qty:
            self.d.text((c[0] + half + 7 * s, c[1]), qty, font=self.fs, fill=INK, anchor="lm")

    def dim(self, p0, p1, text, off=(0, 0), screen=False, color=BLUE, ext=True):
        s = self.s
        a0 = np.asarray(p0 if screen else self.P(p0), float); b0 = np.asarray(p1 if screen else self.P(p1), float)
        o = np.array(off) * s; a, b = a0 + o, b0 + o
        if ext and np.linalg.norm(o) > 0:
            for q0, q in ((a0, a), (b0, b)):
                dd = q - q0; nn = np.linalg.norm(dd)
                if nn > 0:
                    self.d.line([tuple(q0 + dd / nn * 6 * s), tuple(q + dd / nn * 8 * s)], fill=color, width=int(1.2 * s))
        self.d.line([tuple(a), tuple(b)], fill=color, width=int(1.6 * s))
        dvec = b - a; n = np.linalg.norm(dvec)
        if n > 0:
            dvec /= n; p = np.array([-dvec[1], dvec[0]])
            for q, sg in ((a, 1), (b, -1)):
                tip = q; base = q + dvec * sg * 13 * s
                self.d.polygon([tuple(tip), tuple(base + p * 4.5 * s), tuple(base - p * 4.5 * s)], fill=color)
        m = (a + b) / 2
        tw = self.d.textlength(text, font=self.fm)
        self.d.rectangle([m[0] - tw / 2 - 6 * s, m[1] - 12 * s, m[0] + tw / 2 + 6 * s, m[1] + 12 * s], fill="white")
        self.d.text(tuple(m), text, font=self.fm, fill=color, anchor="mm")

    def mark(self, p, size=11, color=(196, 70, 20)):
        s = self.s; a = self.P(p)
        for sg in (1, -1):
            self.d.line([tuple(a + np.array([-size, -size * sg]) * s), tuple(a + np.array([size, size * sg]) * s)], fill=color, width=int(4 * s))

    def text(self, xy, t, big=False):
        self.d.text(tuple(np.array(xy) * self.s), t, font=self.fb if big else self.fs, fill=INK, anchor="mm")

    def big(self, xy, t):
        f = ImageFont.truetype(FONT_B, int(34 * self.s))
        self.d.text(tuple(np.array(xy) * self.s), t, font=f, fill=INK, anchor="mm")


def bubble(main, detail, center, radius, target=None, s=2.0, stroke=3.0):
    """Paste a circular zoom of `detail` (square image) at center (display coords) with leader to target (display)."""
    R = int(radius * s); c = (int(center[0] * s), int(center[1] * s))
    det = detail.resize((2 * R, 2 * R), Image.LANCZOS)
    mask = Image.new("L", (2 * R, 2 * R), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    d = ImageDraw.Draw(main)
    if target is not None:
        t = np.array(target, float) * s
        v = np.array(c, float) - t; v /= np.linalg.norm(v)
        edge = np.array(c, float) - v * R
        d.line([tuple(t), tuple(edge)], fill=INK, width=int(1.8 * s))
        d.ellipse([t[0] - 7 * s, t[1] - 7 * s, t[0] + 7 * s, t[1] + 7 * s], outline=INK, width=int(2 * s))
    main.paste(det, (c[0] - R, c[1] - R), mask)
    d.ellipse([c[0] - R, c[1] - R, c[0] + R, c[1] + R], outline=INK, width=int(stroke * s))
