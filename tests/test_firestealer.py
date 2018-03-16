# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

import unittest

import firestealer


class TestSampleToPoints(unittest.TestCase):

    def test_conversion(self):
        # Samples are successfully converted into InfluxDB points.
        samples = [
            firestealer.Sample('s1', {'tag1': 'value1'}, 42),
            firestealer.Sample('s1', {}, 47),
            firestealer.Sample('s1', {'true': True, 'false': False}, 1.0),
        ]
        points = firestealer.samples_to_points(samples)
        self.assertEqual(bool(points), True)
