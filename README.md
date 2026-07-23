# SAPIENTCOT — SAPIENT to TAK Gateway

Display **SAPIENT** (BSI Flex 335) sensor detections in TAK.

SAPIENT is a general sensor-fusion / ISR interface (widely used in NATO C-UAS,
but not limited to it): sensors report detections of **people, vehicles,
vessels, UAS, and more**.

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
  → CoT `<point>`.
- `classification` (highest-confidence type) → CoT callsign **and CoT battle
  dimension**: person → ground infantry (`a-u-G-U-C-I`), vehicle → ground
  vehicle (`a-u-G-E-V-C`), vessel → sea surface (`a-u-S-X`), drone/UAS → air
  (`a-u-A`); unclassified → unknown ground (`a-u-G`). Set `COT_TYPE` to force one
  type for every detection (e.g. a pure C-UAS laydown).
- `detection_confidence`, classification, and `state` → CoT `<remarks>`.
- **RangeBearing** detections (range/azimuth from the sensor) are resolved to
  lat/lon using the reporting node's location learned from its **StatusReport**.
- **StatusReport** → a sensor-position CoT marker (the sensors themselves on the
  map) with system state + battery.
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
