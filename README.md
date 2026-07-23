# SAPIENTCOT — SAPIENT to TAK Gateway

Display **SAPIENT** (BSI Flex 335 / NATO C-UAS) sensor detections in TAK.

SAPIENTCOT connects to a SAPIENT Fusion / HLDMM node (or middleware), reads
length-delimited protobuf `SapientMessage`s, converts each **DetectionReport**
into Cursor-on-Target, and forwards it to a CoT destination (Mesh SA or a TAK
Server) — the same [PyTAK](https://github.com/snstac/pytak) pipeline as the rest
of the snstac gateway fleet (adsbcot, aiscot, dronecot, aprscot).

```
SAPIENT sensors → Fusion/HLDMM node → sapientcot → COT_URL (TAK)
```

## What it maps

- `SapientMessage.detection_report` → one CoT event per detected object.
- Geographic `Location` (`x`=lon, `y`=lat, `z`=hae; WGS84, degrees or radians)
  → CoT `<point>`. Range/bearing detections are skipped until node-position
  tracking lands.
- `classification` (highest-confidence type) → CoT callsign; air/UAS classes
  keep the configurable air CoT type (default `a-u-A`).
- `detection_confidence`, classification, and `state` → CoT `<remarks>`.
- UID is `SAPIENT.<node_id>.<object_id>` so tracks are stable across reports.

## Install

```bash
sudo apt install sapientcot          # from the snstac apt repository
sudoedit /etc/default/sapientcot     # set COT_URL + SAPIENT_HOST/PORT
sudo systemctl enable --now sapientcot
```

## Configuration

See [`example config`](debian/sapientcot.conf). Key settings: `COT_URL`,
`SAPIENT_HOST`, `SAPIENT_PORT`, `SAPIENT_VERSION` (`v2`/`v1`), `COT_TYPE`,
`COT_STALE`. PyTAK TLS settings apply for `tls://` TAK Server destinations.

## Status

Early (v0.1.0): reads geographic DetectionReports and emits CoT. Roadmap:
SAPIENT registration handshake, range/bearing resolution via node position,
StatusReport → sensor CoT, and Task/Alert handling.

## License

Apache License 2.0. Uses the [`sapient-msg`](https://pypi.org/project/sapient-msg/)
protobuf bindings for the DSTL [SAPIENT-Proto-Files](https://github.com/dstl/SAPIENT-Proto-Files).
