import numpy as np, sys, glob, os
from PIL import Image
a, b = sys.argv[1], sys.argv[2]
for f in sorted(glob.glob(b + "/windlass_*.png")):
    n = os.path.basename(f); x = np.asarray(Image.open(a + "/" + n)); y = np.asarray(Image.open(f))
    if x.shape != y.shape: print(n, "SHAPE", x.shape, y.shape); continue
    da = np.abs(x[..., 3].astype(int) - y[..., 3]); ch = (np.abs(x.astype(int) - y).max(2) > 12)
    ys, xs = np.nonzero(ch)
    print(n, x.shape[:2], "alpha px changed>8: %d" % (da > 8).sum(), "rgb changed px %d" % ch.sum(), "bbox", (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None)
