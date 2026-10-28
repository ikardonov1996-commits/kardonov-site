# Split the working scene into reusable assets that keep the marble veins locked to the stone.
#  Marble_Root (empty) -> Marble_Block, Sculpture_HiRes, MarbleSpace
#  Sculpture_HiRes     -> FaceMask, HandMask   (vein masks follow the statue)
# Writes: asset_statue.blend (statue only), asset_block.blend (block only), asset_all.blend (both).
# usage: blender -b kardonov_block.blend -P make_assets.py -- OUT_DIR
import bpy, sys, os
argv = sys.argv[sys.argv.index("--") + 1:]
out_dir = argv[0]
sc = bpy.context.scene
O = bpy.data.objects

def parent_keep(child, parent):
    mw = child.matrix_world.copy(); child.parent = parent; child.matrix_world = mw

root = O.get("Marble_Root") or O.new("Marble_Root", None)
if root.name not in sc.collection.objects: sc.collection.objects.link(root)
root.empty_display_type = 'ARROWS'; root.empty_display_size = 0.3; root.location = (0, 0, 0)
for name in ("Marble_Block", "Sculpture_HiRes", "MarbleSpace"):
    parent_keep(O[name], root)
for name in ("FaceMask", "HandMask"):
    if name in O: parent_keep(O[name], O["Sculpture_HiRes"])
for o in list(O):
    if o.name.startswith("MarbleSwatch"): O.remove(o)

def save_variant(path, drop):
    hidden = []
    for n in drop:
        if n in O: O[n].hide_render = O[n].hide_viewport = True; hidden.append(n)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True, copy=True)
    for n in hidden: O[n].hide_render = O[n].hide_viewport = False

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "asset_all.blend"), compress=True)
# single-asset files: delete the other object outright (cleaner to append from)
blk = O["Marble_Block"]; O.remove(blk)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "asset_statue.blend"), compress=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(out_dir, "asset_all.blend"))
O = bpy.data.objects
for n in ("Sculpture_HiRes", "FaceMask", "HandMask"):
    if n in O: O.remove(O[n])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "asset_block.blend"), compress=True)
print("ASSETS OK")
