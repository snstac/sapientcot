#!/usr/bin/env python3
# Copyright Sensors & Signals LLC https://www.snstac.com
# SPDX-License-Identifier: Apache-2.0
"""Tests for SAPIENTCOT: SAPIENT DetectionReport -> CoT."""

import unittest

from sapient_msg.bsi_flex_335_v2_0 import sapient_message_pb2 as sm
from sapient_msg.bsi_flex_335_v2_0 import detection_report_pb2 as dr
from sapient_msg.bsi_flex_335_v2_0 import location_pb2 as loc

import sapientcot.functions as fn


def _detection_message():
    msg = sm.SapientMessage()
    msg.node_id = "11111111-1111-1111-1111-111111111111"
    d = msg.detection_report
    d.report_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    d.object_id = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
    d.detection_confidence = 0.87
    d.location.x = -122.25   # lon
    d.location.y = 37.76     # lat
    d.location.z = 120.0     # hae
    d.location.coordinate_system = loc.LOCATION_COORDINATE_SYSTEM_LAT_LNG_DEG_M
    d.location.datum = loc.LOCATION_DATUM_WGS84_E
    c = d.classification.add()
    c.type = "Drone"
    c.confidence = 0.91
    return msg


class SapientCotTestCase(unittest.TestCase):
    def test_detection_to_cot(self):
        cot = fn.sapient_to_cot_xml(_detection_message(), {})
        self.assertIsNotNone(cot)
        self.assertEqual(cot.get("type"), "a-u-A")
        self.assertEqual(
            cot.get("uid"),
            "SAPIENT.11111111-1111-1111-1111-111111111111.01ARZ3NDEKTSV4RRFFQ69G5FAW",
        )
        point = cot.find("point")
        self.assertAlmostEqual(float(point.get("lat")), 37.76, places=4)
        self.assertAlmostEqual(float(point.get("lon")), -122.25, places=4)
        self.assertAlmostEqual(float(point.get("hae")), 120.0, places=1)
        self.assertEqual(cot.find("detail/contact").get("callsign"), "Drone")

    def test_radians_converted(self):
        import math
        msg = _detection_message()
        msg.detection_report.location.x = math.radians(-122.25)
        msg.detection_report.location.y = math.radians(37.76)
        msg.detection_report.location.coordinate_system = (
            loc.LOCATION_COORDINATE_SYSTEM_LAT_LNG_RAD_M
        )
        cot = fn.sapient_to_cot_xml(msg, {})
        self.assertAlmostEqual(float(cot.find("point").get("lat")), 37.76, places=4)

    def test_non_detection_returns_none(self):
        msg = sm.SapientMessage()
        msg.node_id = "n"
        msg.status_report.SetInParent()
        self.assertIsNone(fn.sapient_to_cot_xml(msg, {}))

    def test_range_bearing_skipped(self):
        msg = sm.SapientMessage()
        msg.node_id = "n"
        d = msg.detection_report
        d.object_id = "o"
        d.range_bearing.range = 100.0
        d.range_bearing.azimuth = 45.0
        self.assertIsNone(fn.sapient_to_cot_xml(msg, {}))


if __name__ == "__main__":
    unittest.main()
