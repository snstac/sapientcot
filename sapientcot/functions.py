#!/usr/bin/env python3
# Copyright Sensors & Signals LLC https://www.snstac.com
# SPDX-License-Identifier: Apache-2.0
"""SAPIENTCOT Functions: SAPIENT DetectionReport -> Cursor on Target."""

import math
import xml.etree.ElementTree as ET

from configparser import ConfigParser, SectionProxy
from typing import Optional, Union

import pytak
import sapientcot


def _best_classification(detection) -> tuple:
    """Return (type, confidence) of the highest-confidence classification, or ("", 0)."""
    best = ("", 0.0)
    for cls in getattr(detection, "classification", []):
        conf = cls.confidence if cls.HasField("confidence") else 0.0
        if conf >= best[1] or not best[0]:
            best = (cls.type, conf)
    return best


def _latlon(detection) -> Optional[tuple]:
    """Extract (lat, lon, hae) in WGS84 degrees from a DetectionReport, or None.

    Only the geographic Location oneof is handled (x=lon, y=lat). RangeBearing
    detections need the reporting node's position to resolve and are skipped
    (returned as None) until registration-tracking lands.
    """
    if not detection.HasField("location"):
        return None
    loc = detection.location
    lat, lon = loc.y, loc.x
    hae = loc.z if loc.HasField("z") else 0.0
    # coordinate_system: 1 = deg, 2 = radians (convert).
    if loc.coordinate_system == 2:
        lat, lon = math.degrees(lat), math.degrees(lon)
    return lat, lon, hae


def sapient_to_cot_xml(
    message, config: Union[SectionProxy, dict, None] = None
) -> Optional[ET.Element]:
    """Convert a SAPIENT SapientMessage (DetectionReport) to a CoT Event."""
    config = config or {}
    if not message.HasField("detection_report"):
        return None
    dr = message.detection_report

    ll = _latlon(dr)
    if ll is None:
        return None
    lat, lon, hae = ll

    node_id = message.node_id or "unknown"
    object_id = dr.object_id or dr.report_id
    uid = f"SAPIENT.{node_id}.{object_id}"

    cls_type, cls_conf = _best_classification(dr)
    cot_type = config.get("COT_TYPE", sapientcot.DEFAULT_COT_TYPE)
    cot_stale = int(config.get("COT_STALE", sapientcot.DEFAULT_COT_STALE))

    # A detection classified as air/UAS keeps the (configurable) air type; this
    # is where a deployment can map SAPIENT classes to specific CoT types.
    lc = cls_type.lower()
    if any(k in lc for k in sapientcot.AIR_CLASSES):
        cot_type = config.get("COT_TYPE", sapientcot.DEFAULT_COT_TYPE)

    cot_time = pytak.cot_time()
    event = ET.Element("event")
    event.set("version", "2.0")
    event.set("uid", uid)
    event.set("type", cot_type)
    event.set("how", "m-g")
    event.set("time", cot_time)
    event.set("start", cot_time)
    event.set("stale", pytak.cot_time(cot_stale))

    point = ET.SubElement(event, "point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("hae", str(hae))
    point.set("ce", "9999999.0")
    point.set("le", "9999999.0")

    detail = ET.SubElement(event, "detail")
    contact = ET.SubElement(detail, "contact")
    callsign = cls_type or f"SAPIENT {object_id[:8]}"
    contact.set("callsign", callsign)

    conf = dr.detection_confidence if dr.HasField("detection_confidence") else None
    remarks_parts = [f"SAPIENT node {node_id}"]
    if cls_type:
        remarks_parts.append(f"class={cls_type}" + (f" ({cls_conf:.0%})" if cls_conf else ""))
    if conf is not None:
        remarks_parts.append(f"detection={conf:.0%}")
    if dr.HasField("state") and dr.state:
        remarks_parts.append(f"state={dr.state}")
    remarks = ET.SubElement(detail, "remarks")
    remarks.text = "; ".join(remarks_parts)

    ET.SubElement(detail, "__group").set("name", "Yellow")
    return event


def sapient_to_cot(message, config=None) -> Optional[bytes]:
    """Convert a SAPIENT message to serialized CoT XML bytes, or None."""
    cot = sapient_to_cot_xml(message, config)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)]) if cot is not None else None
    )


def create_tasks(config: ConfigParser, clitool: "pytak.CLITool") -> set:
    """Create the SAPIENTCOT worker task set (PyTAK entry point)."""
    return set([sapientcot.SapientWorker(clitool.tx_queue, config)])
