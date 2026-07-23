#!/usr/bin/env python3
# Copyright Sensors & Signals LLC https://www.snstac.com
# SPDX-License-Identifier: Apache-2.0
"""SAPIENTCOT Constants."""

# SAPIENT node (Fusion/HLDMM or middleware) the gateway reads from.
DEFAULT_SAPIENT_HOST: str = "127.0.0.1"
DEFAULT_SAPIENT_PORT: int = 5010

# CoT event type for a SAPIENT detection/track. SAPIENT is a C-UAS interface, so
# detections default to an unknown air track; classification can promote them.
DEFAULT_COT_TYPE: str = "a-u-A"          # unknown air
DEFAULT_COT_TYPE_HOSTILE: str = "a-h-A-M-F-Q"  # hostile UAS (when classified as such)

# Detections are transient; keep the stale window short by default (seconds).
DEFAULT_COT_STALE: str = "60"

# Classification substrings that mark a detection as an air/UAS track.
AIR_CLASSES = ("drone", "uav", "uas", "quadcopter", "aircraft", "air", "rotary", "fixed wing")

# Wire framing: SAPIENT BSI Flex 335 sends length-delimited protobuf. Default is
# a 4-byte big-endian unsigned length prefix; override via SAPIENT_LEN_BYTES /
# SAPIENT_LEN_ENDIAN if a peer differs.
DEFAULT_LEN_BYTES: int = 4
DEFAULT_LEN_ENDIAN: str = "big"
