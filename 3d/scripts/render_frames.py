# Render given frames (fast EEVEE) from the animation camera.
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
out, frames = argv[0], [int(x) for x in argv[1].split(",")]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = int(argv[2]) if len(argv) > 2 else 8
sc.render.resolution_x = 600; sc.render.resolution_y = 800
for f in frames:
    sc.frame_set(f); sc.render.filepath = "%s/f_%04d.png" % (out, f); bpy.ops.render.render(write_still=True)
