# The Ebony replacer's assemble.build_arrow, with the atlas names as parameters (its own are the ebony atlases'): splices
# stage_arrow.py's shapes into vanilla's ebonyarrow.nif (Arrow:0 the loose arrow; ArrowQuiver:0 the quiver body,
# ArrowQuiver:1 an added shape for its collar and fang plate; Arrow1..Arrow6 the six quiver arrows, one shape each - the
# game hides them by name) and ebonyarrowprojectile.nif (EbonyArrowFlight:0); both collision boxes refitted.
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import niflib
from assemble import shape, only_shape, geometry_tail, splice, give_shader, add_shape, parent_of, set_box, drop_orphans, save
import struct


def build_arrow(van_path, flight_path, out_arrow, out_flight, shapes_dir, loy_dir, arrow_atlas, body_atlas, trim_atlas):
    rep = {}
    n = niflib.Nif(van_path)
    an, ab = only_shape(os.path.join(shapes_dir, "arrow.nif")); arrow_tail = geometry_tail(an, ab)
    a0 = shape(n, "Arrow:0"); splice(n, a0, arrow_tail); give_shader(n, a0, loy_dir, arrow_atlas)
    q0 = shape(n, "ArrowQuiver:0"); qn, qb = only_shape(os.path.join(shapes_dir, "quiver_%s.nif" % body_atlas))
    splice(n, q0, geometry_tail(qn, qb)); give_shader(n, q0, loy_dir, body_atlas)
    tn, tb = only_shape(os.path.join(shapes_dir, "quiver_%s.nif" % trim_atlas))
    trim = add_shape(n, q0, geometry_tail(tn, tb), "ArrowQuiver:1", parent_of(n, q0)); give_shader(n, trim, loy_dir, trim_atlas)
    for k in range(1, 7):
        b = shape(n, "Arrow%d" % k); sn, sb = only_shape(os.path.join(shapes_dir, "quiver_Arrow%d.nif" % k))
        assert parent_of(n, b) == parent_of(n, q0)
        splice(n, b, geometry_tail(sn, sb)); give_shader(n, b, loy_dir, arrow_atlas)
    bodies = {}
    for co in [i for i, t in enumerate(n.btypes) if t == "bhkCollisionObject"]:
        node, _, body = struct.unpack_from("<iHi", n.blocks[co], 0); bodies[n.name(node)] = body
    rep["collision"] = {"Arrow (root) - the loose arrow": set_box(n, bodies["Arrow"], np.load(os.path.join(shapes_dir, "points_arrow.npy"))),
                        "ArrowQuiver - the quiver": set_box(n, bodies["ArrowQuiver"], np.load(os.path.join(shapes_dir, "points_quiver.npy")))}
    rep["orphans_dropped"] = drop_orphans(n); save(n, out_arrow); rep["blocks"] = len(n.blocks)
    f = niflib.Nif(flight_path); b = shape(f, "EbonyArrowFlight:0"); splice(f, b, arrow_tail); give_shader(f, b, loy_dir, arrow_atlas)
    co = [i for i, t in enumerate(f.btypes) if t == "bhkCollisionObject"][0]; body = struct.unpack_from("<iHi", f.blocks[co], 0)[2]
    rep["flight"] = {"collision": set_box(f, body, np.load(os.path.join(shapes_dir, "points_arrow.npy"))), "orphans_dropped": drop_orphans(f)}
    save(f, out_flight); rep["flight"]["blocks"] = len(f.blocks)
    return rep
