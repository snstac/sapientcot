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


def _cot_type_for(cls_type: str, config) -> str:
    """Map a SAPIENT classification string to a CoT type (battle dimension).

    An explicit `COT_TYPE` in config, when set, forces the type for every
    detection (e.g. a pure C-UAS deployment). Otherwise the classification drives
    it (air / ground / vehicle / person / sea), falling back to DEFAULT_COT_TYPE
    (unknown ground) — SAPIENT is general ISR, not only C-UAS.
    """
    forced = config.get("COT_TYPE")
    if forced:
        return forced
    lc = (cls_type or "").lower()
    for keywords, cot in sapientcot.CLASS_COT_TYPES:
        if any(k in lc for k in keywords):
            return cot
    return sapientcot.DEFAULT_COT_TYPE


_EARTH_R = 6378137.0  # WGS84 semi-major axis (m)


def _location_to_latlon(loc) -> tuple:
    """(lat, lon, hae) in WGS84 degrees from a SAPIENT Location (x=lon, y=lat)."""
    lat, lon = loc.y, loc.x
    hae = loc.z if loc.HasField("z") else 0.0
    if loc.coordinate_system == 2:  # radians
        lat, lon = math.degrees(lat), math.degrees(lon)
    return lat, lon, hae


def _rb_normalize(rb) -> tuple:
    """(azimuth_deg, range_m, elevation_deg) from a RangeBearing, unit-normalized."""
    az, rng = rb.azimuth, rb.range
    elev = rb.elevation if rb.HasField("elevation") else 0.0
    cs = rb.coordinate_system  # 1=deg/m 2=rad/m 3=deg/km 4=rad/km
    if cs in (2, 4):  # radians -> degrees
        az, elev = math.degrees(az), math.degrees(elev)
    if cs in (3, 4):  # km -> m
        rng *= 1000.0
    return az, rng, elev


def _project(lat, lon, hae, az_deg, range_m, elev_deg) -> tuple:
    """Destination point from (lat,lon,hae) along az_deg (from true north), range_m."""
    lat1, lon1, brng = math.radians(lat), math.radians(lon), math.radians(az_deg)
    ground = range_m * math.cos(math.radians(elev_deg)) if elev_deg else range_m
    dr = ground / _EARTH_R
    lat2 = math.asin(math.sin(lat1) * math.cos(dr) + math.cos(lat1) * math.sin(dr) * math.cos(brng))
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(dr) * math.cos(lat1),
        math.cos(dr) - math.sin(lat1) * math.sin(lat2),
    )
    hae2 = hae + (range_m * math.sin(math.radians(elev_deg)) if elev_deg else 0.0)
    return math.degrees(lat2), math.degrees(lon2), hae2


def _latlon(detection, node_loc=None) -> Optional[tuple]:
    """(lat, lon, hae) WGS84 degrees for a DetectionReport, or None.

    Geographic Location is used directly. A RangeBearing detection is resolved
    against the reporting node's location (node_loc = (lat,lon,hae) from its most
    recent StatusReport); without a known node location it returns None. Datum
    note: magnetic/grid north are treated as true north (no declination applied).
    """
    if detection.HasField("location"):
        return _location_to_latlon(detection.location)
    if detection.HasField("range_bearing") and node_loc is not None:
        az, rng, elev = _rb_normalize(detection.range_bearing)
        return _project(node_loc[0], node_loc[1], node_loc[2], az, rng, elev)
    return None


def node_location_from_status(message) -> Optional[tuple]:
    """(lat, lon, hae) of a reporting node from a StatusReport, or None."""
    if not message.HasField("status_report"):
        return None
    sr = message.status_report
    if not sr.HasField("node_location"):
        return None
    return _location_to_latlon(sr.node_location)


def sapient_to_cot_xml(
    message, config: Union[SectionProxy, dict, None] = None, node_locations=None
) -> Optional[ET.Element]:
    """Convert a SAPIENT SapientMessage (DetectionReport) to a CoT Event.

    node_locations: optional {node_id: (lat, lon, hae)} for resolving RangeBearing
    detections against the reporting node's most recent StatusReport location.
    """
    config = config or {}
    if not message.HasField("detection_report"):
        return None
    dr = message.detection_report

    node_id = message.node_id or "unknown"
    node_loc = (node_locations or {}).get(message.node_id)
    ll = _latlon(dr, node_loc)
    if ll is None:
        return None
    lat, lon, hae = ll

    object_id = dr.object_id or dr.report_id
    uid = f"SAPIENT.{node_id}.{object_id}"

    cls_type, cls_conf = _best_classification(dr)
    cot_stale = int(config.get("COT_STALE", sapientcot.DEFAULT_COT_STALE))
    cot_type = _cot_type_for(cls_type, config)

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


def sapient_to_cot(message, config=None, node_locations=None) -> Optional[bytes]:
    """Convert a SAPIENT DetectionReport message to serialized CoT XML bytes, or None."""
    cot = sapient_to_cot_xml(message, config, node_locations)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)]) if cot is not None else None
    )


# SAPIENT StatusReport.System enum -> CoT how/label (1=OK, 2=WARNING, 3=ERROR, 5=GOODBYE).
_SYSTEM_LABELS = {0: "unspecified", 1: "OK", 2: "WARNING", 3: "ERROR", 5: "GOODBYE"}


def status_to_cot_xml(message, config=None) -> Optional[ET.Element]:
    """Convert a SAPIENT StatusReport into a sensor-position CoT Event, or None.

    Puts the reporting node (sensor) itself on the map from StatusReport
    node_location, with its system state and battery level in remarks. Friendly
    ground sensor marker (a-f-G-E-S). No node_location -> None.
    """
    config = config or {}
    loc = node_location_from_status(message)
    if loc is None:
        return None
    lat, lon, hae = loc
    node_id = message.node_id or "unknown"
    sr = message.status_report

    cot_time = pytak.cot_time()
    # Sensor markers stale slower than detections; reuse COT_STALE * 5, min 300s.
    stale = max(300, int(config.get("COT_STALE", sapientcot.DEFAULT_COT_STALE)) * 5)
    event = ET.Element("event")
    event.set("version", "2.0")
    event.set("uid", f"SAPIENT.node.{node_id}")
    event.set("type", config.get("SENSOR_COT_TYPE", sapientcot.DEFAULT_SENSOR_COT_TYPE))
    event.set("how", "m-g")
    event.set("time", cot_time)
    event.set("start", cot_time)
    event.set("stale", pytak.cot_time(stale))

    point = ET.SubElement(event, "point")
    point.set("lat", str(lat))
    point.set("lon", str(lon))
    point.set("hae", str(hae))
    point.set("ce", "9999999.0")
    point.set("le", "9999999.0")

    detail = ET.SubElement(event, "detail")
    ET.SubElement(detail, "contact").set("callsign", f"SAPIENT {node_id[:8]}")
    parts = [f"SAPIENT node {node_id}", f"system={_SYSTEM_LABELS.get(sr.system, sr.system)}"]
    if sr.HasField("mode") and sr.mode:
        parts.append(f"mode={sr.mode}")
    if sr.HasField("power") and sr.power.HasField("level"):
        parts.append(f"power={sr.power.level}%")
    ET.SubElement(detail, "remarks").text = "; ".join(parts)
    ET.SubElement(detail, "__group").set("name", "Cyan")
    return event


def status_to_cot(message, config=None) -> Optional[bytes]:
    """Serialize a StatusReport sensor CoT to XML bytes, or None."""
    cot = status_to_cot_xml(message, config)
    return (
        b"\n".join([pytak.DEFAULT_XML_DECLARATION, ET.tostring(cot)]) if cot is not None else None
    )


def create_tasks(config: ConfigParser, clitool: "pytak.CLITool") -> set:
    """Create the SAPIENTCOT worker task set (PyTAK entry point)."""
    return set([sapientcot.SapientWorker(clitool.tx_queue, config)])
