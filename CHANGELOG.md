## SAPIENTCOT 0.1.3

- Resolve **RangeBearing** detections: track each reporting node's location from
  its StatusReport and project range/azimuth/elevation to lat/lon, so radar / RF
  / acoustic sensors (which report bearing, not lat/lon) now produce CoT instead
  of being dropped. (Magnetic/grid north treated as true north.)
- **StatusReport -> sensor CoT**: put the SAPIENT sensors/nodes themselves on the
  map (friendly ground sensor a-f-G-E-S) with system state + battery in remarks.
- New helpers: node_location_from_status, status_to_cot; DEFAULT_SENSOR_COT_TYPE.

## SAPIENTCOT 0.1.2

- General ISR classification -> CoT battle-dimension mapping (SAPIENT is not only
  C-UAS): person -> ground infantry, vehicle -> ground vehicle, vessel -> sea
  surface, drone/UAS -> air; unclassified falls back to unknown **ground**
  (default type changed a-u-A -> a-u-G). `COT_TYPE` still forces one type.

## SAPIENTCOT 0.1.1

- Fix wire framing: SAPIENT length prefix is 4-byte **little-endian** (per the DSTL
  Apex middleware `struct.pack("<I", ...)`), not big-endian. The v0.1.0 default
  would fail to decode a real SAPIENT feed. Added a framing regression test.

## SAPIENTCOT 0.1.0

- Initial release: SAPIENT (BSI Flex 335) C-UAS → TAK gateway on PyTAK.
- `SapientWorker` reads length-delimited protobuf `SapientMessage`s from a
  Fusion/HLDMM node (configurable framing) using the `sapient-msg` bindings.
- `sapient_to_cot` maps `DetectionReport` (geographic `Location`, classification,
  confidence) to Cursor-on-Target; stable `SAPIENT.<node>.<object>` UIDs.
- Supports BSI Flex 335 v2 (default) and v1.
- Debian packaging (service + `/etc/default/sapientcot`); tests for the mapping.
