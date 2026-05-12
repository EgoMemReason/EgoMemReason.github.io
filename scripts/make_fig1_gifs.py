#!/usr/bin/env python3
"""Build the Figure 1 timeline GIFs for the EgoMemReason project page.

For each timeline frame shown in fig1.pdf we take the EgoLife frame nearest the
labelled timestamp plus the frames ~1s before and after (3 frames, 1 FPS) from
the relevant wearer's egocentric view, and write a full-resolution looping GIF
to static/fig1/<dayN>_<HHMMSS>.gif.
"""
import json
import os
import sys
from PIL import Image

INDEX = "/nas-ssd2/video_datasets/EgoLife/egolife_frames_index.json"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "fig1")
FRAME_MS = 500  # per-frame duration -> ~1.5s loop for 3 frames

# (day, "HHMMSS" target, wearer)  -- order = left-to-right on the timeline
TIMELINE = [
    ("DAY1", "141723", "A5_KATRINA"),   # behavior
    ("DAY2", "155853", "A6_SHURE"),     # event
    ("DAY2", "182339", "A6_SHURE"),     # entity (+ event + behavior)
    ("DAY3", "120120", "A6_SHURE"),     # entity (+ event + behavior)
    ("DAY3", "212233", "A6_SHURE"),     # behavior
    ("DAY4", "105035", "A6_SHURE"),     # event query (+ behavior)
    ("DAY4", "132725", "A6_SHURE"),     # entity query (+ behavior)
    ("DAY5", "120758", "A5_KATRINA"),   # behavior
    ("DAY6", "192049", "A6_SHURE"),     # behavior frame
    ("DAY7", "120824", "A5_KATRINA"),   # behavior
]


def hhmmss_to_centi(s):
    return int(s) * 100  # HHMMSS -> HHMMSScc


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(INDEX) as f:
        idx = json.load(f)

    manifest = []
    for day, target, wearer in TIMELINE:
        frames = [fr for fr in idx[wearer] if fr["day"] == day]
        frames.sort(key=lambda fr: fr["time"])
        tt = hhmmss_to_centi(target)
        # nearest frame
        center_i = min(range(len(frames)), key=lambda i: abs(frames[i]["time"] - tt))
        diff_s = abs(frames[center_i]["time"] - tt) / 100.0
        # pick 3 consecutive frames centered on it (clamp at segment edges)
        lo = max(0, center_i - 1)
        hi = min(len(frames), lo + 3)
        lo = max(0, hi - 3)
        chosen = frames[lo:hi]

        imgs = [Image.open(fr["path"]).convert("RGB") for fr in chosen]
        # normalise size to the center frame's size
        w, h = imgs[1 if len(imgs) > 1 else 0].size
        imgs = [im if im.size == (w, h) else im.resize((w, h)) for im in imgs]

        out_name = f"{day.lower()}_{target}.gif"
        out_path = os.path.join(OUT_DIR, out_name)
        imgs[0].save(
            out_path,
            save_all=True,
            append_images=imgs[1:],
            duration=FRAME_MS,
            loop=0,
            optimize=True,
        )
        size_kb = os.path.getsize(out_path) / 1024
        rec = {
            "out": out_name,
            "day": day,
            "label": f"{target[:2]}:{target[2:4]}:{target[4:6]}",
            "wearer": wearer,
            "nframes": len(imgs),
            "center_time": frames[center_i]["time"],
            "diff_s": diff_s,
            "res": [w, h],
            "size_kb": round(size_kb, 1),
            "paths": [fr["path"] for fr in chosen],
        }
        manifest.append(rec)
        print(f"{out_name:24s} wearer={wearer:11s} center={frames[center_i]['time']:>9d} "
              f"diff={diff_s:7.2f}s n={len(imgs)} {w}x{h} {size_kb:7.1f}KB")

    with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    total = sum(r["size_kb"] for r in manifest)
    print(f"\nTotal: {total/1024:.2f} MB across {len(manifest)} GIFs")
    if any(r["diff_s"] > 5 for r in manifest):
        print("WARNING: some frames are >5s off their labelled timestamp:")
        for r in manifest:
            if r["diff_s"] > 5:
                print(f"  {r['out']}: {r['diff_s']:.1f}s off")


if __name__ == "__main__":
    sys.exit(main())
