# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

import math
from unittest import (
    mock,
    TestCase,
)

import firestealer


class TestSampleToPoints(TestCase):

    def test_conversion(self):
        # Samples are successfully converted into InfluxDB points.
        samples = [
            firestealer.Sample('s1', {'tag1': 'value1'}, 42),
            firestealer.Sample('s2', {}, 47),
            firestealer.Sample('s3', {'true': True, 'false': False}, 1.0),
        ]
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow = lambda: 'now'
            points = firestealer.samples_to_points(samples)
        self.assertEqual(points, ({
            'measurement': 's1',
            'tags': {'tag1': 'value1'},
            'fields': {'value': 42},
            'time': 'now',
        }, {
            'measurement': 's2',
            'tags': {},
            'fields': {'value': 47},
            'time': 'now',
        }, {
            'measurement': 's3',
            'tags': {'true': True, 'false': False},
            'fields': {'value': 1.0},
            'time': 'now',
        }))

    def test_same_time(self):
        # The same timestamp is used for all points.
        samples = [
            firestealer.Sample('s1', {'tag1': 'value1'}, 42),
            firestealer.Sample('s2', {}, 47),
            firestealer.Sample('s3', {'true': True, 'false': False}, 1.0),
        ]
        points = firestealer.samples_to_points(samples)
        times = set(point['time'] for point in points)
        self.assertEqual(len(times), 1)
        self.assertNotEqual(list(times)[0], '')

    def test_not_a_number(self):
        # Samples with invalid values are discarded.
        samples = [
            firestealer.Sample('s1', {}, math.nan),
            firestealer.Sample('s2', {}, 47),
        ]
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow = lambda: 'now'
            points = firestealer.samples_to_points(samples)
        self.assertEqual(points, ({
            'measurement': 's2',
            'tags': {},
            'fields': {'value': 47},
            'time': 'now',
        },))

    def test_no_samples(self):
        # Without samples, there are no points.
        self.assertEqual(firestealer.samples_to_points([]), ())
