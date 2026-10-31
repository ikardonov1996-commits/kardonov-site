import sys, numpy as np; from PIL import Image
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert("RGBA")).astype(float); h = a.shape[0]
    m = a[..., 3:4] / 255; c = a[..., :3] * m          # premultiplied
    d = np.abs(np.diff(c, axis=0)).mean(axis=(1, 2))   # d[r] = row r vs r+1
    out = []
    for k in range(1, 16):
        r = h - k * h // 16 - 1                         # boundary (rows from top)
        nb = np.r_[d[r-6:r-1], d[r+2:r+7]].mean()
        out.append(f"{d[r]/max(nb,1e-3):.2f}")
    print(f.split('/')[-1], a.shape, "alpha>0 %.1f%%" % (100*(a[...,3]>0).mean()), "seam ratios", " ".join(out), "max", a[...,:3][a[...,3]>250].max())
