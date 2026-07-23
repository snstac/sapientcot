## SAPIENTCOT 0.1.0

- Initial release: SAPIENT (BSI Flex 335) C-UAS → TAK gateway on PyTAK.
- `SapientWorker` reads length-delimited protobuf `SapientMessage`s from a
  Fusion/HLDMM node (configurable framing) using the `sapient-msg` bindings.
- `sapient_to_cot` maps `DetectionReport` (geographic `Location`, classification,
  confidence) to Cursor-on-Target; stable `SAPIENT.<node>.<object>` UIDs.
- Supports BSI Flex 335 v2 (default) and v1.
- Debian packaging (service + `/etc/default/sapientcot`); tests for the mapping.
