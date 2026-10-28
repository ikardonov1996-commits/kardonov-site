# KARDONOV David — reference notes

## Statue / anatomy (use now)
- statue_turnaround.jpg — 5 side views + top. Target for nipples (small, nearly flat),
  navel (recessed, vertical oval), overall marble look, rough rock base.

## Marble (use now)
- Warm cream / pinkish-ivory body, orange-ochre crack-network veins, some clustered and thicker,
  hairline branches in between. Honed finish: soft sheen, not lacquer. Rough rock plinth with
  chipped facets and same veins. (Refs were sent inline: pink statue on green; statue with
  robot arm on grey; rough marble podium with orange veins.)

## Later — NOT now
- Neural interface: glowing amber/gold headband around the head with round emitter modules
  (front centre, temples, back). Head turnaround sheet: FRONT, 3/4 L, L profile, BACK,
  R profile, 3/4 R, TOP, BOTTOM. Use head views (without the band) as face reference.
- Robotic arm: replaces statue's RIGHT arm (viewer's left), shoulder to fingers. White/ivory
  plates, gold trim, dark grey joints, blue glowing joints/lines, round blue shoulder emitter.
  Sheet has front / medial / lateral / back views, shoulder close-ups, hand close-ups in pose.
- Order: finish base model + carving animation first, then interface, then robo-arm.

## Asset structure (keep reusable!)
- assets/asset_statue.blend — statue only (1M polys, marble, Face/Hand vein masks parented to it)
- assets/asset_block.blend — raw block only (same marble, fracture/joint attributes)
- assets/asset_all.blend — both, aligned (block contains statue, >= 9 mm clearance)
- Hierarchy: Marble_Root -> Marble_Block, Sculpture_HiRes, MarbleSpace. MOVE THE ROOT, never MarbleSpace
  alone: veins are in MarbleSpace coordinates, so they stay locked to the stone only if it moves with it.
- Carving animation goes into its own file and appends from the assets (doesn't modify them).

## Later scenes / tasks — NOT now
- Block: tie with rope, lower/raise it with a hand windlass crane (well-bucket style winch: drum + crank,
  rope winds onto the drum). Needs rope rig around the block + winch model.
- Statue: neural-interface headband (see above), robotic right arm (see above), face expression tweaks.
