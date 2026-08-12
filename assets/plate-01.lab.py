#!/usr/bin/env python3
"""Wet Proof art lab.

One mass, one boundary, one residue field, in the Plectis plum world.
Every mark is downstream of a process: pigment channels with different
mobilities advected through a curl-noise flow inside a resist silhouette,
deposits accumulating where flow meets the boundary, droplet fallout whose
density decays away from the body, contamination where channels overlap.

Usage:
  repo-python art_lab.py --seed 5 --scale 0.5 --out draft5.png
"""
import argparse
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from PIL import Image

# ---------------- noise ----------------

def value_noise(rng, shape, cells, octaves=4, persistence=0.55):
    h, w = shape
    out = np.zeros(shape, dtype=np.float64)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        c = cells * (2 ** o)
        grid = rng.standard_normal((c + 2, int(c * w / h) + 2))
        gy = np.linspace(0, grid.shape[0] - 1.001, h)
        gx = np.linspace(0, grid.shape[1] - 1.001, w)
        Y, X = np.meshgrid(gy, gx, indexing="ij")
        y0, x0 = np.floor(Y).astype(int), np.floor(X).astype(int)
        fy, fx = Y - y0, X - x0
        fy = fy * fy * (3 - 2 * fy)
        fx = fx * fx * (3 - 2 * fx)
        v = (grid[y0, x0] * (1 - fy) * (1 - fx) + grid[y0 + 1, x0] * fy * (1 - fx)
             + grid[y0, x0 + 1] * (1 - fy) * fx + grid[y0 + 1, x0 + 1] * fy * fx)
        out += amp * v
        total += amp
        amp *= persistence
    out /= total
    return (out - out.min()) / (out.max() - out.min() + 1e-9)


def curl_field(rng, shape, cells=3, octaves=4, strength=1.0):
    psi = value_noise(rng, shape, cells, octaves)
    gy, gx = np.gradient(psi)
    u, v = gy, -gx  # divergence-free
    m = np.sqrt(u * u + v * v).mean() + 1e-9
    return u / m * strength, v / m * strength

# ---------------- advection ----------------

def advect(field, u, v, dt):
    h, w = field.shape
    Y, X = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    return map_coordinates(field, [Y - v * dt, X - u * dt], order=1, mode="nearest")

# ---------------- main plate ----------------

def render(seed, W, H):
    rng = np.random.default_rng(seed)
    S = H / 800.0  # scale factor for pixel-sized constants

    # ---- ground: plum void with slow cloud ----
    ground = np.zeros((H, W, 3))
    ground[..., 0], ground[..., 1], ground[..., 2] = 0x17 / 255, 0x10 / 255, 0x20 / 255
    cloud = value_noise(rng, (H, W), 2, 3)
    cloud = gaussian_filter(cloud, 40 * S)
    cloud = (cloud - cloud.mean())
    ground[..., 0] += cloud * 0.012
    ground[..., 2] += cloud * 0.030
    ground[..., 1] += cloud * 0.008

    # ---- body silhouette: warped superellipse, cropped by left/bottom ----
    cy, cx = 0.55 * H, 0.72 * W
    ry, rx = 0.33 * H, 0.26 * W
    Y, X = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    wy = ((value_noise(rng, (H, W), 2, 2) - 0.5) * 0.45
          + (value_noise(rng, (H, W), 5, 2) - 0.5) * 0.10) * H
    wx = ((value_noise(rng, (H, W), 2, 2) - 0.5) * 0.45
          + (value_noise(rng, (H, W), 5, 2) - 0.5) * 0.10) * W
    d = (((Y + wy - cy) / ry) ** 2 + ((X + wx - cx) / rx) ** 2)
    body = np.clip(1.35 - d, 0, None)
    body = np.clip(body, 0, 1.0)
    body = gaussian_filter(body, 3 * S)
    support = body > 0.06

    # interior resist islands: wax spots pigment cannot enter
    resist = np.zeros((H, W))
    n_isl = 7
    ys = rng.uniform(cy - 0.6 * ry, min(cy + 0.6 * ry, H - 1), n_isl)
    xs = rng.uniform(max(cx - 0.6 * rx, 0), min(cx + 0.6 * rx, W - 1), n_isl)
    rs = rng.uniform(9, 26, n_isl) * S
    for yy, xx, rr in zip(ys, xs, rs):
        m = ((Y - yy) ** 2 + (X - xx) ** 2) < rr ** 2
        resist[m] = 1.0
    resist = gaussian_filter(resist, 1.5 * S)
    body_open = body * (1 - 0.9 * resist)

    # ---- pigment channels seeded inside the body ----
    base = value_noise(rng, (H, W), 5, 4)
    ridge = 1 - np.abs(2 * value_noise(rng, (H, W), 3, 3) - 1)
    folds = 0.55 + 0.75 * ridge
    core = np.clip(0.55 - d, 0, 1) * 2.2
    amber = body_open * (np.clip(1.2 - d * 1.1, 0, 1) * (0.55 + 0.8 * base) + core) * folds * 1.2
    ring = np.clip(1.0 - np.abs(d - 0.75) * 2.2, 0, 1)
    verm = body_open * ring * (0.45 + 0.9 * value_noise(rng, (H, W), 6, 3))
    flank = np.clip((X - cx) / rx, 0, 1.4) * body_open
    mag = flank * (0.4 + 0.9 * value_noise(rng, (H, W), 4, 3)) * folds

    # ---- advect with per-channel mobility (chromatographic separation) ----
    u, v = curl_field(rng, (H, W), cells=3, octaves=4, strength=2.6 * S)
    u += 0.9 * S  # gentle drift up-right
    v -= 0.7 * S
    edge = np.abs(gaussian_filter(body, 2 * S) - gaussian_filter(body, 6 * S))
    edge = edge / (edge.max() + 1e-9)
    deposit = np.zeros((H, W))
    steps = 46
    for i in range(steps):
        amber = advect(amber, u, v, 0.6)
        verm = advect(verm, u, v, 1.0)
        mag = advect(mag, u, v, 1.5)
        # pigment cannot leave the body: the silhouette is the resist
        amber *= (0.06 + 0.94 * (body_open > 0.05))
        verm *= (0.06 + 0.94 * (body_open > 0.05))
        mag *= (0.06 + 0.94 * (body_open > 0.05))
        # deposit where pigment meets the boundary: rims, dried edges
        deposit += (amber + verm + 1.4 * mag) * edge * 0.02
    deposit = np.clip(gaussian_filter(deposit, 1.2 * S), 0, 3)

    # granulation
    gran = 0.82 + 0.36 * value_noise(rng, (H, W), 60, 2)
    amber *= gran
    verm *= 0.9 + 0.3 * value_noise(rng, (H, W), 50, 2)
    mag *= gran

    for a in (amber, verm, mag):
        np.clip(a, 0, 2.2, out=a)

    # ---- cool boundary arc: petrol band entering top-left, wrapping the flank ----
    t = np.linspace(0, 1, 700)
    p0 = np.array([0.58 * W, 1.12 * H])
    p1 = np.array([0.30 * W, 0.48 * H])
    p2 = np.array([0.64 * W, -0.10 * H])
    bez = ((1 - t)[:, None] ** 2 * p0 + 2 * ((1 - t) * t)[:, None] * p1 + t[:, None] ** 2 * p2)
    band = np.zeros((H, W))
    band_in = np.zeros((H, W))
    spark = np.zeros((H, W))
    bw = (26 + 48 * (1 - t) + 18 * np.sin(t * 6 + 1.1)) * S  # wide at entry, thin as it climbs
    # tangent -> inner normal (the side facing the mass, +x when climbing)
    tang = np.gradient(bez, axis=0)
    tnorm = tang / (np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9)
    nrm = np.stack([-tnorm[:, 1], tnorm[:, 0]], axis=1)
    nrm *= np.where(nrm[:, :1] < 0, -1.0, 1.0)  # point roughly +x, toward the body
    for i, ((px, py), w_) in enumerate(zip(bez, bw)):
        climb = i / len(bez)
        for layer, off, wf, gain in ((band, 0.0, 1.0, 1.0), (band_in, 0.42 * w_, 0.38, 0.25 + 0.75 * climb)):
            qx, qy = px + nrm[i, 0] * off, py + nrm[i, 1] * off
            ww = w_ * wf
            ix0, ix1 = int(max(qx - ww * 2, 0)), int(min(qx + ww * 2, W - 1))
            iy0, iy1 = int(max(qy - ww * 2, 0)), int(min(qy + ww * 2, H - 1))
            if ix0 >= ix1 or iy0 >= iy1:
                continue
            yy, xx = np.meshgrid(np.arange(iy0, iy1), np.arange(ix0, ix1), indexing="ij")
            dd = np.sqrt((yy - qy) ** 2 + (xx - qx) ** 2) / ww
            layer[iy0:iy1, ix0:ix1] = np.maximum(layer[iy0:iy1, ix0:ix1], np.clip(1 - dd, 0, 1) * gain)
        # sparkle specks caught on the inner lip
        if i % 9 == 0 and rng.uniform() < 0.5:
            sx, sy = px + nrm[i, 0] * 0.75 * w_, py + nrm[i, 1] * 0.75 * w_
            rr = rng.uniform(1.2, 3.2) * S
            ix0, ix1 = int(max(sx - rr * 3, 0)), int(min(sx + rr * 3, W - 1))
            iy0, iy1 = int(max(sy - rr * 3, 0)), int(min(sy + rr * 3, H - 1))
            if ix0 < ix1 and iy0 < iy1:
                yy, xx = np.meshgrid(np.arange(iy0, iy1), np.arange(ix0, ix1), indexing="ij")
                g = np.exp(-((yy - sy) ** 2 + (xx - sx) ** 2) / (rr ** 2)) ** 1.4
                spark[iy0:iy1, ix0:ix1] = np.maximum(spark[iy0:iy1, ix0:ix1], g)
    # wobble the band so its edges are organic, then granulate
    for _ in range(3):
        band = advect(band, u, v, 1.2)
        band_in = advect(band_in, u, v, 1.2)
        spark = advect(spark, u, v, 0.6)
    band = gaussian_filter(band, 1.2 * S)
    band *= 0.75 + 0.5 * value_noise(rng, (H, W), 8, 3)
    band *= (1 - 0.25 * np.clip(body, 0, 1))  # translucent past the mass: contaminate, not vanish
    band_in = gaussian_filter(band_in, 0.9 * S) * (1 - 0.2 * np.clip(body, 0, 1))
    band_core = np.clip(band * 1.4 - 0.25, 0, 1)
    # thin interference line along the inner edge (oil film)
    gyb, gxb = np.gradient(gaussian_filter(band, 2.5 * S))
    iline = np.clip(np.abs(gyb) + np.abs(gxb), 0, None)
    iline = iline / (iline.max() + 1e-9)
    iline = np.clip(iline - 0.30, 0, 1) * 2.2
    iline *= (value_noise(rng, (H, W), 4, 2) > 0.45)  # the film catches only in patches

    # ---- residue field: fallout whose density decays from the body ----
    from scipy.ndimage import distance_transform_edt
    dist = distance_transform_edt(~support)
    droplet = np.zeros((H, W))
    pale = np.zeros((H, W))
    n_drop = int(2400 * (W / 2560))
    # accept-reject: density ~ exp(-dist/sigma), with an up-right plume
    sigma = 0.16 * H
    cand_y = rng.uniform(0, H - 1, n_drop * 6)
    cand_x = rng.uniform(0, W - 1, n_drop * 6)
    plume = np.exp(-((cand_x / W - 0.42) ** 2 + (cand_y / H - 0.16) ** 2) / 0.07)
    pd = np.exp(-dist[cand_y.astype(int), cand_x.astype(int)] / sigma) + 0.10 * plume
    keep = rng.uniform(0, 1, cand_y.shape) < pd
    cy_d, cx_d = cand_y[keep][:n_drop], cand_x[keep][:n_drop]
    sizes = np.exp(rng.normal(0.15, 0.75, cy_d.shape)) * 1.6 * S
    for yy, xx, rr in zip(cy_d, cx_d, sizes):
        far = dist[int(yy), int(xx)] > 0.22 * H
        rr = min(rr, (7 if far else 26) * S)
        iy0, iy1 = int(max(yy - rr * 2.5, 0)), int(min(yy + rr * 2.5, H - 1))
        ix0, ix1 = int(max(xx - rr * 2.5, 0)), int(min(xx + rr * 2.5, W - 1))
        if ix0 >= ix1 or iy0 >= iy1:
            continue
        ys2, xs2 = np.meshgrid(np.arange(iy0, iy1), np.arange(ix0, ix1), indexing="ij")
        g = np.exp(-((ys2 - yy) ** 2 + (xs2 - xx) ** 2) / (rr ** 2 + 1e-9)) ** 1.6
        near_edge = dist[int(yy), int(xx)] < 0.10 * H and dist[int(yy), int(xx)] > 0
        if rr > 10 * S and near_edge and rng.uniform() < 0.7:
            pale[iy0:iy1, ix0:ix1] = np.maximum(pale[iy0:iy1, ix0:ix1], g)
        else:
            droplet[iy0:iy1, ix0:ix1] = np.maximum(droplet[iy0:iy1, ix0:ix1], g)
    # one shared wobble so drops are not perfect gaussians
    droplet = advect(droplet, u, v, 2.0)
    pale = advect(pale, u, v, 0.8)
    # rims: darker ring at drop edges (coffee ring)
    dgy, dgx = np.gradient(gaussian_filter(droplet + pale, 1.0 * S))
    rim = np.sqrt(dgy ** 2 + dgx ** 2)
    rim = rim / (rim.max() + 1e-9)

    # ---- scratches: a few hairline arcs ----
    scratch = np.zeros((H, W))
    for _ in range(2):
        sy = rng.uniform(0.1, 0.9) * H
        sx = rng.uniform(0.1, 0.9) * W
        ln = rng.uniform(0.1, 0.3) * W
        ang = rng.uniform(0, np.pi)
        tt = np.linspace(0, 1, int(ln))
        cxx = sx + np.cos(ang) * ln * tt + 30 * S * np.sin(tt * 5)
        cyy = sy + np.sin(ang) * ln * tt * 0.4
        ok = (cxx > 0) & (cxx < W - 1) & (cyy > 0) & (cyy < H - 1)
        scratch[cyy[ok].astype(int), cxx[ok].astype(int)] = 1.0
    scratch = gaussian_filter(scratch, 0.6 * S)
    scratch *= (body < 0.4) * (band < 0.25)

    # ---- text-safe calm zones, wide feather ----
    rail = np.zeros((H, W))
    rail[int(0.04 * H):int(0.94 * H), int(0.02 * W):int(0.44 * W)] = 1
    rail = gaussian_filter(rail, 0.05 * W)
    calm = np.clip(rail, 0, 1)
    droplet *= (1 - 0.9 * calm)
    pale *= (1 - 0.8 * calm)
    rim *= (1 - 0.8 * calm)
    band_core *= (1 - 0.8 * rail)
    band *= (1 - 0.75 * rail)
    band_in *= (1 - 0.8 * rail)
    spark *= (1 - 0.9 * rail)
    iline *= (1 - 0.85 * rail)
    scratch *= (1 - 0.9 * calm)
    amber *= (1 - 0.35 * rail)
    verm *= (1 - 0.35 * rail)
    mag *= (1 - 0.35 * rail)
    deposit *= (1 - 0.6 * rail)

    # ---- composite ----
    img = ground.copy()

    # pigment colours (backlit liquid): contaminated additive
    A = np.clip(amber, 0, 1.8)
    V = np.clip(verm, 0, 1.8)
    M = np.clip(mag, 0, 1.8)
    col_a = np.array([0.95, 0.62, 0.13])
    col_v = np.array([0.88, 0.26, 0.10])
    col_m = np.array([0.78, 0.12, 0.36])
    pig = (A[..., None] * col_a + V[..., None] * col_v + M[..., None] * col_m)
    # contamination: strong overlaps go dirty brown, not brighter
    overlap = np.clip(A * V + V * M + A * M, 0, 3)
    dirty = np.array([0.42, 0.23, 0.12])
    mixw = np.clip(overlap * 0.35, 0, 0.75)[..., None]
    tot = np.clip(A + V + M, 0, 4)
    lum = 1 - np.exp(-tot * 1.05)
    pigc = pig / (tot[..., None] + 1e-6)
    pigc = pigc * (1 - mixw) + dirty * mixw
    body_rgb = pigc * lum[..., None]
    inner = gaussian_filter(np.clip(body_rgb, 0, 1), 10 * S) * 0.18 * body[..., None]
    img = 1 - (1 - img) * (1 - np.clip(body_rgb + inner, 0, 1.2) * 0.97)  # screen, backlit

    # dried edge deposit: darken toward blood-rust at rims of the mass
    dep = np.clip(deposit * 0.65, 0, 1)[..., None]
    rust = np.array([0.30, 0.075, 0.05])
    img = img * (1 - dep) + rust * dep

    # cool band: deep petrol multiply + faint additive blue + interference line
    petrol = np.array([0.05, 0.13, 0.26])
    ultr = np.array([0.13, 0.30, 0.85])
    bandN = np.clip(band, 0, 1)[..., None]
    img = img * (1 - bandN * 0.7) + petrol * bandN * 0.7
    img = 1 - (1 - img) * (1 - ultr * np.clip(band_core, 0, 1)[..., None] * 0.55)
    inlip = np.array([0.22, 0.62, 0.88])
    img = 1 - (1 - img) * (1 - inlip * np.clip(band_in, 0, 1)[..., None] * 0.6)
    sparkc = np.array([0.87, 0.96, 0.93])
    img = 1 - (1 - img) * (1 - sparkc * np.clip(spark, 0, 1)[..., None] * 0.8)
    film = np.array([0.18, 0.75, 0.70])
    img = 1 - (1 - img) * (1 - film * np.clip(iline, 0, 1)[..., None] * 0.62)

    # residue: carriers stain with local pigment, bone when far from the body
    carry = np.clip(gaussian_filter(body_rgb, 6 * S), 0, 1)
    bone = np.array([0.86, 0.79, 0.66])
    farw = np.clip(dist / (0.5 * H), 0, 1)[..., None]
    drop_col = carry * (1 - farw) + bone * farw * 0.9
    dN = np.clip(droplet, 0, 1)[..., None]
    img = 1 - (1 - img) * (1 - drop_col * dN * 0.85)
    # pale large drops: cream wash with rusty rim
    cream = np.array([0.90, 0.84, 0.72])
    pN = np.clip(pale, 0, 1)[..., None]
    img = 1 - (1 - img) * (1 - cream * pN * 0.5)
    rimN = np.clip(rim * 1.6, 0, 1)[..., None]
    rimc = np.array([0.34, 0.10, 0.06])
    img = img * (1 - rimN * 0.62) + rimc * rimN * 0.62

    # scratches: faint bright hairlines
    scr = np.clip(scratch * 1.2, 0, 1)[..., None]
    img = 1 - (1 - img) * (1 - np.array([0.7, 0.66, 0.6]) * scr * 0.35)

    # ---- finish: grain, vignette, gamut compression ----
    g = rng.standard_normal((H, W, 1)) * 0.012 + rng.standard_normal((H, W, 3)) * 0.004
    img = img + g * (0.35 + 0.65 * np.clip(img.mean(axis=2, keepdims=True) * 2, 0, 1))
    vign = 1 - 0.16 * ((Y / H - 0.5) ** 2 + (X / W - 0.5) ** 2)[..., None] * 2
    img *= vign
    img = np.clip(img, 0, 1) ** 1.03
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--out", default="plate.png")
    ap.add_argument("--jpg-quality", type=int, default=0, help="if >0, write JPEG at this quality")
    a = ap.parse_args()
    W, H = int(2560 * a.scale), int(1600 * a.scale)
    img = render(a.seed, W, H)
    im = Image.fromarray(img)
    if a.jpg_quality:
        im.convert("RGB").save(a.out, quality=a.jpg_quality, optimize=True, progressive=True)
    else:
        im.save(a.out)
    print("wrote", a.out, W, "x", H)
