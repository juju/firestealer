# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

import unittest

from firestealer import (
    influx,
    prometheus,
)


class TestToPoints(unittest.TestCase):

    def test_conversion(self):
        # Samples are successfully converted into InfluxDB points.
        samples = [
            prometheus.Sample('s1', {'tag1': 'value1'}, 42),
            prometheus.Sample('s1', {}, 47),
            prometheus.Sample('s1', {'true': True, 'false': False}, 1.0),
        ]
        points = influx.to_points(samples)
        self.assertEqual(bool(points), True)
