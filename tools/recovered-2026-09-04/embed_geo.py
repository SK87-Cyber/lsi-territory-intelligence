#!/usr/bin/env python3
"""Trim the us-atlas TopoJSON down to the eight Southeast states and embed it.

Why: the site loads Census boundaries from a CDN at run time and falls back to
stylized shapes when that fails. Embedding removes the dependency entirely.

Usage:
    python3 embed_geo.py states-10m.json counties-10m.json [--tol 0.004]

Writes geo-se.json next to this script. build.py injects it into the built page
at __GEO_JSON__; if the file is absent the placeholder becomes null and the page
falls back to the CDN exactly as before.
"""
import json, sys, os

SE_FIPS = {"37": "NC", "45": "SC", "13": "GA", "01": "AL",
           "28": "MS", "47": "TN", "21": "KY", "05": "AR"}


def decode(topo, layer):
    """TopoJSON -> [{id, coords}] with coords as [[ring,...],...] in lon/lat."""
    tr = topo.get("transform")
    sx, sy = (tr["scale"] if tr else (1, 1))
    ox, oy = (tr["translate"] if tr else (0, 0))
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        out = []
        for dx, dy in arc:
            if tr:
                x += dx; y += dy
                out.append([x * sx + ox, y * sy + oy])
            else:
                out.append([dx, dy])
        arcs.append(out)

    def ring(idxs):
        pts = []
        for i in idxs:
            a = arcs[~i][::-1] if i < 0 else arcs[i]
            pts.extend(a[1:] if pts else a)
        return pts

    feats = []
    for g in topo["objects"][layer]["geometries"]:
        t = g.get("type")
        if t == "Polygon":
            coords = [[ring(r) for r in g["arcs"]]]
        elif t == "MultiPolygon":
            coords = [[ring(r) for r in poly] for poly in g["arcs"]]
        else:
            continue
        feats.append({"id": str(g.get("id", "")).zfill(2 if layer == "states" else 5),
                      "name": (g.get("properties") or {}).get("name", ""),
                      "polys": coords})
    return feats


def simplify(pts, tol):
    """Douglas-Peucker. Rings keep their first and last point."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        d2 = dx * dx + dy * dy
        worst, wi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            if d2 == 0:
                dist = (px - ax) ** 2 + (py - ay) ** 2
            else:
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / d2))
                qx, qy = ax + t * dx, ay + t * dy
                dist = (px - qx) ** 2 + (py - qy) ** 2
            if dist > worst:
                worst, wi = dist, i
        if worst > tol * tol and wi > 0:
            keep[wi] = True
            stack.append((a, wi)); stack.append((wi, b))
    return [p for p, k in zip(pts, keep) if k]


def shrink(feats, tol, nd=4):
    out = []
    for f in feats:
        polys = []
        for poly in f["polys"]:
            rings = []
            for r in poly:
                s = simplify(r, tol)
                if len(s) >= 4:
                    rings.append([[round(x, nd), round(y, nd)] for x, y in s])
            if rings:
                polys.append(rings)
        if polys:
            out.append({"id": f["id"], "name": f["name"], "polys": polys})
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 0.004
    st = decode(json.load(open(args[0])), "states")
    ct = decode(json.load(open(args[1])), "counties")
    st = [f for f in st if f["id"] in SE_FIPS]
    ct = [f for f in ct if f["id"][:2] in SE_FIPS]
    data = {"states": shrink(st, tol), "counties": shrink(ct, tol)}
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "geo-se.json")
    json.dump(data, open(p, "w"), separators=(",", ":"))
    pts = sum(len(r) for g in (data["states"] + data["counties"]) for poly in g["polys"] for r in poly)
    print(f"wrote {p}: {len(data['states'])} states, {len(data['counties'])} counties, "
          f"{pts:,} points, {os.path.getsize(p):,} bytes (tol={tol})")
