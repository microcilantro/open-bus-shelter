"""Tiny z-buffer renderer for the open bus shelter concept.

Units: inches. x along curb (roof 0..120), y from back of walk toward street, z up.
"""
import sys
import numpy as np
from PIL import Image

# ---------------------------------------------------------------- scene ----
TRIS = []      # (v0, v1, v2, face_id, kind)  kind: 0 opaque, 1 panel
FACES = []     # per face: (albedo rgb, normal)
_obj = [0]


def _face(quad, color, kind=0, normal=None, group=None):
    q = [np.array(p, float) for p in quad]
    if normal is None:
        n = np.cross(q[1] - q[0], q[2] - q[0])
        n = n / (np.linalg.norm(n) + 1e-12)
    else:
        n = np.array(normal, float)
    if group is None:
        fid = len(FACES)
        FACES.append((np.array(color, float), n))
    else:
        fid = group
    TRIS.append((q[0], q[1], q[2], fid, kind))
    if len(q) == 4:
        TRIS.append((q[0], q[2], q[3], fid, kind))
    return fid


def prism(v, color, kind=0):
    """v: 8 vertices, bottom 0..3 then top 4..7 (same order)."""
    v = [np.array(p, float) for p in v]
    c = sum(v) / 8
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for f in faces:
        q = [v[i] for i in f]
        n = np.cross(q[1] - q[0], q[2] - q[0])
        n = n / (np.linalg.norm(n) + 1e-12)
        fc = sum(q) / 4
        if np.dot(n, fc - c) < 0:
            q = q[::-1]
            n = -n
        _face(q, color, kind, n)


def box(x0, x1, y0, y1, z0, z1, color, kind=0):
    prism([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
           (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], color, kind)


def sloped(x0, x1, y0, y1, zfn, t, color, kind=0):
    a, b = zfn(x0), zfn(x1)
    prism([(x0, y0, a), (x1, y0, b), (x1, y1, b), (x0, y1, a),
           (x0, y0, a + t), (x1, y0, b + t), (x1, y1, b + t), (x0, y1, a + t)], color, kind)


def between(p0, p1, w, t, color):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    a = np.array([1.0, 0, 0])
    b = np.cross(d, a); b /= np.linalg.norm(b)
    ha, hb = a * w / 2, b * t / 2
    prism([p0 - ha - hb, p0 + ha - hb, p0 + ha + hb, p0 - ha + hb,
           p1 - ha - hb, p1 + ha - hb, p1 + ha + hb, p1 - ha + hb], color)


GROUP = {}


def ground_group(name, color, normal=(0, 0, 1)):
    if name not in GROUP:
        GROUP[name] = len(FACES)
        FACES.append((np.array(color, float), np.array(normal, float)))
    return GROUP[name]


def tiles(x0, x1, y0, y1, z, color, name, step=24):
    g = ground_group(name, color)
    xs = np.arange(x0, x1, step); ys = np.arange(y0, y1, step)
    for x in xs:
        for y in ys:
            xa, ya = min(x + step, x1), min(y + step, y1)
            _face([(x, y, z), (xa, y, z), (xa, ya, z), (x, ya, z)], color, 0, (0, 0, 1), g)


# ------------------------------------------------------------- materials ----
STEEL = (0.70, 0.72, 0.75)
STEEL_DK = (0.58, 0.60, 0.63)
CONC = (0.82, 0.80, 0.76)
CURB = (0.76, 0.75, 0.72)
ASPH = (0.32, 0.33, 0.35)
GRASS = (0.50, 0.61, 0.40)
HEDGE = (0.30, 0.45, 0.28)
WALL = (0.87, 0.82, 0.73)
GLASS = (0.36, 0.45, 0.54)
WOOD = (0.56, 0.41, 0.30)
SIGN = (0.10, 0.33, 0.64)
WHITE = (0.95, 0.95, 0.95)
PERSON = (0.44, 0.49, 0.57)
PANEL = (0.80, 0.87, 0.94)


def u(x):  # underside of beams (top of arms): 8'-6" at x=0 rising to 9'-4" at x=120
    return 102 + 10 * x / 120


def build(walk=60, bench=False, person="stand"):
    S = 1.625
    # ground and context
    tiles(-240, 360, 0, walk, 0, CONC, "walk")
    tiles(-240, 360, walk, walk + 420, -6, ASPH, "street", 36)
    g = ground_group("curbface", CURB, (0, 1, 0))
    for x in range(-240, 360, 24):
        _face([(x, walk, 0), (x, walk, -6), (x + 24, walk, -6), (x + 24, walk, 0)], CURB, 0, (0, 1, 0), g)
    # lane line
    for x in range(-240, 360, 60):
        box(x, x + 30, walk + 150, walk + 154, -6, -5.9, WHITE)
    tiles(-240, 360, -60, 0, 0.5, GRASS, "grass")
    box(-240, 360, -48, -24, 0, 34, HEDGE)
    box(-240, 360, -160, -140, 0, 300, WALL)
    for i in range(-3, 6):
        for zz in (40, 150):
            box(i * 60 + 6, i * 60 + 42, -141, -138.8, zz, zz + 70, GLASS)

    for xc in (12, 108):
        # post: two struts back to back
        box(xc - S / 2, xc + S / 2, 4.375, 7.625, 0, 123.5, STEEL)
        # base angles
        box(xc - S / 2, xc + S / 2, 7.625, 11.125, 0, 0.25, STEEL_DK)
        box(xc - S / 2, xc + S / 2, 7.625, 7.875, 0, 3.5, STEEL_DK)
        box(xc - S / 2, xc + S / 2, 0.875, 4.375, 0, 0.25, STEEL_DK)
        box(xc - S / 2, xc + S / 2, 4.125, 4.375, 0, 3.5, STEEL_DK)
        for ya in (1.5, 3.375, 8.625, 10.5):
            box(xc - 0.4, xc + 0.4, ya - 0.4, ya + 0.4, 0.25, 0.65, (0.25, 0.26, 0.28))
        # cantilever arm beside the post (inner side) and knee brace
        ax = xc + S if xc < 60 else xc - S
        zt = u(ax)
        box(ax - S / 2, ax + S / 2, 0, 48, zt - S, zt, STEEL)
        between((ax, 7.625, zt - S - 17), (ax, 7.625 + 17, zt - S), S, S, STEEL)
    # beams on arms
    sloped(0, 120, 0, S, u, S, STEEL)
    sloped(0, 120, 48 - S, 48, u, S, STEEL)
    # purlins on beams
    for xp in (0, 36 - S / 2, 60 - S / 2, 84 - S / 2, 120 - S):
        z0 = u(xp + S / 2) + S
        box(xp, xp + S, 0, 48, z0, z0 + S, STEEL)
    # roof panels (translucent)
    sloped(-0.5, 120.5, -1, 49.5, lambda x: u(x) + 2 * S, 0.5, PANEL, kind=1)
    # leaning rail / backrest rail
    box(0, 120, 7.625, 9.25, 30.4, 32, STEEL)
    # stop sign on post 1 extension
    box(4, 20, 7.625, 8.0, 109, 125, SIGN)
    box(5, 19, 8.0, 8.1, 119.5, 123.5, WHITE)

    if bench:
        box(0, 120, 7.625, 9.25, 14.875, 16.5, STEEL)          # seat rail
        for xa in (22, 46, 70):
            box(xa - S / 2, xa + S / 2, 7.625, 31.625, 16.5, 18.125, STEEL)
        for xa in (22, 70):
            box(xa - S / 2, xa + S / 2, 30, 31.625, 0, 24, STEEL)      # leg / armrest post
            box(xa - S / 2, xa + S / 2, 9.25, 31.625, 24, 25.625, STEEL)  # armrest
        for xa in (22, 70):
            box(xa - S / 2, xa + S / 2, 9.25, 10.875, 16.5, 40.5, STEEL)  # back upright
        for y0 in (12, 18, 24):
            box(20, 72, y0, y0 + 5.5, 18.125, 19.125, WOOD)
        for z0 in (24, 30.5):
            box(20, 72, 10.875, 11.875, z0, z0 + 5.5, WOOD)

    if person == "stand":
        px, py = 72, 22
        box(px - 4, px - 0.6, py, py + 4, 0, 32, PERSON)
        box(px + 0.6, px + 4, py, py + 4, 0, 32, PERSON)
        box(px - 5, px + 5, py - 1, py + 5, 32, 56, PERSON)
        box(px - 7, px - 5, py, py + 4, 34, 54, PERSON)
        box(px + 5, px + 7, py, py + 4, 34, 54, PERSON)
        box(px - 2.5, px + 2.5, py - 0.5, py + 4.5, 57.5, 65.5, PERSON)
    elif person == "sit":
        px = 36
        box(px - 5, px + 5, 11, 17, 19.125, 42, PERSON)
        box(px - 2.5, px + 2.5, 11.5, 16.5, 43.5, 51.5, PERSON)
        box(px - 4.5, px - 0.5, 15, 30, 19.125, 23.5, PERSON)
        box(px + 0.5, px + 4.5, 15, 30, 19.125, 23.5, PERSON)
        box(px - 4.5, px - 0.5, 27, 31, 0, 19.125, PERSON)
        box(px + 0.5, px + 4.5, 27, 31, 0, 19.125, PERSON)
        box(px - 7, px - 5, 12, 22, 26, 40, PERSON)
        box(px + 5, px + 7, 12, 22, 26, 40, PERSON)


# ------------------------------------------------------------ rasterizer ----
def look_at(eye, target, up=(0, 0, 1)):
    eye, target, up = map(lambda a: np.array(a, float), (eye, target, up))
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    d = np.cross(f, r)   # screen-down
    return np.stack([r, d, f])  # rows: x(right), y(down), z(forward)


def raster(tri_pts, ids, W, H, persp=True):
    """tri_pts: (N,3,3) in screen coords (sx, sy, depth). Returns zbuf, idbuf."""
    zb = np.full((H, W), np.inf)
    ib = np.full((H, W), -1, int)
    for k in range(len(tri_pts)):
        p = tri_pts[k]
        if persp and np.any(p[:, 2] <= 1.0):
            continue
        x0 = max(int(np.floor(p[:, 0].min())), 0); x1 = min(int(np.ceil(p[:, 0].max())), W - 1)
        y0 = max(int(np.floor(p[:, 1].min())), 0); y1 = min(int(np.ceil(p[:, 1].max())), H - 1)
        if x0 > x1 or y0 > y1:
            continue
        xs = np.arange(x0, x1 + 1) + 0.5; ys = np.arange(y0, y1 + 1) + 0.5
        X, Y = np.meshgrid(xs, ys)
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = p
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        w0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
        w1 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        if persp:
            z = 1.0 / (w0 / az + w1 / bz + w2 / cz)
        else:
            z = w0 * az + w1 * bz + w2 * cz
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = m & (z < sub)
        sub[upd] = z[upd]
        ib[y0:y1 + 1, x0:x1 + 1][upd] = ids[k]
    return zb, ib


def render(eye, target, out, W=1600, H=1000, ss=2, fov=40, sun=(-0.45, 0.55, 0.75)):
    W2, H2 = W * ss, H * ss
    R = look_at(eye, target)
    E = np.array(eye, float)
    f = (W2 / 2) / np.tan(np.radians(fov / 2))
    cx, cy = W2 / 2, H2 / 2

    V = np.array([[t[0], t[1], t[2]] for t in TRIS])          # (N,3,3)
    fid = np.array([t[3] for t in TRIS])
    kind = np.array([t[4] for t in TRIS])
    C = (V - E) @ R.T                                           # camera coords
    S = np.empty_like(C)
    S[..., 2] = C[..., 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        S[..., 0] = cx + f * C[..., 0] / C[..., 2]
        S[..., 1] = cy + f * C[..., 1] / C[..., 2]

    op = kind == 0
    zb, ib = raster(S[op], fid[op], W2, H2)
    zp, ipb = raster(S[~op], fid[~op], W2, H2)

    # light-space shadow maps (orthographic)
    L = np.array(sun, float); L /= np.linalg.norm(L)
    lu = np.cross(L, (0, 0, 1)); lu /= np.linalg.norm(lu)
    lv = np.cross(L, lu)
    LM = np.stack([lu, lv, -L])
    SM = 2048
    allv = V.reshape(-1, 3)
    near = allv[(np.abs(allv[:, 0] - 60) < 260) & (allv[:, 1] > -170) & (allv[:, 1] < 300)]
    P = near @ LM.T
    lo, hi = P[:, :2].min(0), P[:, :2].max(0)
    scale = (SM - 4) / (hi - lo).max()

    def to_light(pts):
        q = pts @ LM.T
        q[..., 0] = (q[..., 0] - lo[0]) * scale + 2
        q[..., 1] = (q[..., 1] - lo[1]) * scale + 2
        return q
    LV = to_light(V)
    szo, _ = raster(LV[op], fid[op], SM, SM, persp=False)
    szp, _ = raster(LV[~op], fid[~op], SM, SM, persp=False)

    def world_from(z):
        jj, ii = np.meshgrid(np.arange(W2) + 0.5, np.arange(H2) + 0.5)
        xc = (jj - cx) / f * z; yc = (ii - cy) / f * z
        cam = np.stack([xc, yc, z], -1)
        return cam @ R + E

    def shadow(Pw, bias=2.0):
        q = to_light(Pw.reshape(-1, 3))
        u_ = np.clip(q[:, 0].astype(int), 0, SM - 1); v_ = np.clip(q[:, 1].astype(int), 0, SM - 1)
        d = q[:, 2]
        inside = (q[:, 0] >= 0) & (q[:, 0] < SM) & (q[:, 1] >= 0) & (q[:, 1] < SM)
        s = np.ones(len(d))
        o = inside & (d - bias > szo[v_, u_])
        tp = inside & (d - bias > szp[v_, u_])
        s[tp] = 0.62
        s[o] = 0.0
        return s.reshape(Pw.shape[:2])

    alb = np.array([fc[0] for fc in FACES]); nrm = np.array([fc[1] for fc in FACES])
    hit = ib >= 0
    zsafe = np.where(hit, zb, 1.0)
    Pw = world_from(zsafe)
    sh = shadow(Pw)
    idx = np.where(hit, ib, 0)
    ndl = np.clip(nrm[idx] @ L, 0, 1)
    sky_n = 0.5 + 0.5 * nrm[idx][..., 2]
    light = 0.38 + 0.14 * sky_n + 0.62 * ndl * sh
    col = alb[idx] * light[..., None]

    # sky gradient
    t = (np.arange(H2) / H2)[:, None, None]
    sky = (1 - t) * np.array([0.70, 0.80, 0.91]) + t * np.array([0.93, 0.95, 0.97])
    sky = np.broadcast_to(sky, (H2, W2, 3))
    # haze
    dist = np.where(hit, zb, 1e9)
    hz = np.clip((dist - 500) / 2600, 0, 0.6)[..., None]
    col = np.where(hit[..., None], col * (1 - hz) + sky * hz, sky)

    # edges on opaque geometry
    e = np.zeros((H2, W2), bool)
    e[:, :-1] |= (ib[:, :-1] != ib[:, 1:])
    e[:-1, :] |= (ib[:-1, :] != ib[1:, :])
    zl = np.where(hit, zb, 1e6)
    e[:, :-1] |= np.abs(zl[:, :-1] - zl[:, 1:]) > 0.04 * np.minimum(zl[:, :-1], zl[:, 1:])
    e[:-1, :] |= np.abs(zl[:-1, :] - zl[1:, :]) > 0.04 * np.minimum(zl[:-1, :], zl[1:, :])
    near_ok = hit & (zl < 900)
    col = np.where((e & near_ok)[..., None], col * 0.42, col)

    # translucent roof panels
    ph = (ipb >= 0) & (zp < zb)
    Pp = world_from(np.where(ph, zp, 1.0))
    pidx = np.where(ph, ipb, 0)
    pn = nrm[pidx]
    pndl = np.abs(pn @ L)
    corr = 0.88 + 0.12 * np.sin(2 * np.pi * Pp[..., 1] / 2.67)
    pcol = alb[pidx] * (0.62 + 0.38 * pndl)[..., None] * corr[..., None]
    a = 0.62
    col = np.where(ph[..., None], col * (1 - a) + pcol * a, col)
    pe = np.zeros((H2, W2), bool)
    pe[:, :-1] |= ph[:, :-1] != ph[:, 1:]
    pe[:-1, :] |= ph[:-1, :] != ph[1:, :]
    col = np.where(pe[..., None], col * 0.5, col)

    img = np.clip(col, 0, 1) ** (1 / 1.05)
    im = Image.fromarray((img * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    im.save(out, optimize=True)
    print("wrote", out, len(TRIS), "tris")


def reset():
    TRIS.clear(); FACES.clear(); GROUP.clear()


if __name__ == "__main__":
    which = sys.argv[1]
    outdir = sys.argv[2]
    if which == "a":   # no bench, front 3/4 from street left
        build(walk=60, bench=False, person="stand")
        render((-150, 330, 78), (62, 20, 62), f"{outdir}/r1_nobench_front.png")
    elif which == "b":  # no bench, side profile showing cantilever
        build(walk=60, bench=False, person="none")
        render((-235, 135, 82), (48, 24, 66), f"{outdir}/r2_nobench_side.png", fov=40)
    elif which == "c":  # bench, front 3/4 from street right
        build(walk=84, bench=True, person="sit")
        render((260, 340, 76), (58, 22, 52), f"{outdir}/r3_bench_front.png")
    elif which == "d":  # bench, closer eye-level view
        build(walk=84, bench=True, person="none")
        render((150, 170, 54), (46, 16, 30), f"{outdir}/r4_bench_close.png", fov=46)
