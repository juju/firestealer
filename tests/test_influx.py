# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

import math
from unittest import (
    mock,
    TestCase,
)

from . import helpers
import firestealer


class TestWriteToInflux(TestCase):

    def test_error_bad_conn_string(self):
        # An InfluxError is raised when the provided connection string is not
        # well formed.
        with self.assertRaises(firestealer.InfluxError) as ctx:
            firestealer.write_to_influx('bad-wolf', samples)
        self.assertEqual(
            str(ctx.exception),
            "invalid InfluxDB connection string 'bad-wolf'")

    def test_error_client(self):
        # An InfluxError is raised if it is not possible to create a DB client.
        with helpers.patch_influx() as (mock_client, _):
            mock_client.side_effect = ValueError('bad wolf')
            with self.assertRaises(firestealer.InfluxError) as ctx:
                firestealer.write_to_influx(
                    'who:tardis@1.2.3.4:4242/mydb', samples)
        self.assertEqual(
            str(ctx.exception), 'cannot write to InfluxDB: bad wolf')

    def test_error_write_points(self):
        # An InfluxError is raised if writing points does not succeed.
        with helpers.patch_influx() as (_, mock_write):
            mock_write.side_effect = ValueError('bad wolf')
            with self.assertRaises(firestealer.InfluxError) as ctx:
                firestealer.write_to_influx(
                    'who:tardis@1.2.3.4:4242/mydb', samples)
        self.assertEqual(
            str(ctx.exception), 'cannot write to InfluxDB: bad wolf')

    def test_success(self):
        # Points are successfully written.
        with helpers.patch_influx() as (mock_client, mock_write):
            with mock.patch('datetime.datetime') as mock_datetime:
                mock_datetime.utcnow = lambda: 'right now'
                firestealer.write_to_influx(
                    'who:tardis@1.2.3.4:4242/db', samples)
        mock_client.assert_called_once_with(
            database='db', host='1.2.3.4', password='tardis', port=4242,
            username='who')
        mock_write.assert_called_once_with(({
            'measurement': 's1',
            'fields': {'value': 42},
            'time': 'right now',
            'tags': {'tag1': 'value1'},
        }, {
            'measurement': 's2',
            'fields': {'value': 47},
            'time': 'right now',
            'tags': {},
        }, {
            'measurement': 's3',
            'fields': {'value': 1.0},
            'time': 'right now',
            'tags': {'true': True, 'false': False},
        }))


class TestSampleToPoints(TestCase):

    def test_conversion(self):
        # Samples are successfully converted into InfluxDB points.
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


samples = (
    firestealer.Sample('s1', {'tag1': 'value1'}, 42),
    firestealer.Sample('s2', {}, 47),
    firestealer.Sample('s3', {'true': True, 'false': False}, 1.0),
)
