#!/usr/bin/env python3
# Copyright Sensors & Signals LLC https://www.snstac.com
# SPDX-License-Identifier: Apache-2.0
"""SAPIENTCOT Constants."""

# SAPIENT node (Fusion/HLDMM or middleware) the gateway reads from.
DEFAULT_SAPIENT_HOST: str = "127.0.0.1"
DEFAULT_SAPIENT_PORT: int = 5010

# Fallback CoT type for an unclassified SAPIENT detection. SAPIENT is a GENERAL
# sensor-fusion / ISR interface (people, vehicles, vessels, UAS, ...), not just
# C-UAS — so the neutral fallback is an unknown *ground* track, and the
# classification table below promotes air / sea / vehicle / person as detected.
DEFAULT_COT_TYPE: str = "a-u-G"          # unknown ground
# Optional operator override to force a hostile affiliation (unused by default;
# SAPIENT reports classification, not affiliation — that's a fusion decision).
DEFAULT_COT_TYPE_HOSTILE: str = "a-h-A-M-F-Q"

# Detections are transient; keep the stale window short by default (seconds).
DEFAULT_COT_STALE: str = "60"

# CoT type for a SAPIENT sensor/node marker (from StatusReport) — friendly ground
# equipment sensor. Override with SENSOR_COT_TYPE.
DEFAULT_SENSOR_COT_TYPE: str = "a-f-G-E-S"

# SAPIENT DetectionReportClassification.type is free text. Map common substrings
# to a MIL-STD-2525 CoT battle dimension (unknown affiliation). First match wins.
CLASS_COT_TYPES = (
    (("drone", "uav", "uas", "quadcopter", "multirotor", "rotary", "fixed wing",
      "fixed-wing", "aircraft", "helicopter", "rotor"), "a-u-A"),                  # air
    (("person", "people", "human", "pedestrian", "dismount", "infantry",
      "walker", "crowd"), "a-u-G-U-C-I"),                                          # ground: infantry
    (("vehicle", "car", "truck", "van", "motorcycle", "lorry", "bus", "tank",
      "apc", "jeep", "suv", "quad bike"), "a-u-G-E-V-C"),                          # ground: vehicle
    (("vessel", "ship", "boat", "maritime", "watercraft", "surface craft",
      "kayak", "jetski", "rib"), "a-u-S-X"),                                       # sea surface
    (("animal", "dog", "deer", "bird", "livestock", "wildlife"), "a-u-G"),         # ground: animal
)

# Back-compat: the air keyword set (first CLASS_COT_TYPES entry).
AIR_CLASSES = CLASS_COT_TYPES[0][0]

# Wire framing: SAPIENT BSI Flex 335 sends length-delimited protobuf with a
# 4-byte LITTLE-endian unsigned length prefix (per the DSTL Apex middleware:
# `struct.pack("<I", len)` / `struct.unpack("<I", ...)`, matching protobuf's
# little-endian convention). Override via SAPIENT_LEN_BYTES / SAPIENT_LEN_ENDIAN
# only for a non-standard peer.
DEFAULT_LEN_BYTES: int = 4
DEFAULT_LEN_ENDIAN: str = "little"
