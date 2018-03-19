# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

from contextlib import contextmanager
from io import StringIO
import math
import ssl
from unittest import (
    mock,
    TestCase,
)

from . import helpers
import firestealer


class TestFSteal(TestCase):

    success_tests = [{
        'about': 'no samples',
        'args': ['http://1.2.3.4/metrics'],
    }, {
        'about': 'all samples',
        'args': ['http://1.2.3.4/metrics'],
        'text': helpers.example_text,
        'want_output': """
jujushell_containers_duration_bucket
  le=5 operation=create-container --> 2.0
  le=10 operation=create-container --> 6.0
  le=+Inf operation=create-container --> 7.0
jujushell_containers_duration_sum
  operation=create-container --> 27.648935921
jujushell_containers_duration_count
  operation=create-container --> 7.0
jujushell_containers_in_flight --> 7.0
jujushell_errors_count
  message=cannot authenticate user --> 5.0
jujushell_requests_count
  code=200 --> 33.0
jujushell_requests_duration
  code=200 quantile=0.99 --> nan
jujushell_requests_in_flight --> 0.0
process_cpu_seconds_total --> 316.83
process_max_fds --> 1024.0
"""[1:],
    }, {
        'about': 'text output with prefix',
        'args': ['http://1.2.3.4/metrics', '--add-prefix', 'prod-'],
        'text': helpers.example_text,
        'want_output': """
prod-jujushell_containers_duration_bucket
  le=5 operation=create-container --> 2.0
  le=10 operation=create-container --> 6.0
  le=+Inf operation=create-container --> 7.0
prod-jujushell_containers_duration_sum
  operation=create-container --> 27.648935921
prod-jujushell_containers_duration_count
  operation=create-container --> 7.0
prod-jujushell_containers_in_flight --> 7.0
prod-jujushell_errors_count
  message=cannot authenticate user --> 5.0
prod-jujushell_requests_count
  code=200 --> 33.0
prod-jujushell_requests_duration
  code=200 quantile=0.99 --> nan
prod-jujushell_requests_in_flight --> 0.0
prod-process_cpu_seconds_total --> 316.83
prod-process_max_fds --> 1024.0
"""[1:],
    }, {
        'about': 'match multiple samples',
        'args': ['http://4.3.2.1/metrics', '-m', 'in_flight'],
        'text': helpers.example_text,
        'want_output': """
jujushell_containers_in_flight --> 7.0
jujushell_requests_in_flight --> 0.0
"""[1:],
    }, {
        'about': 'match multiple samples with prefix',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'process_cpu|fds',
            '--add-prefix', 'staging_'],
        'text': helpers.example_text,
        'want_output': """
staging_process_cpu_seconds_total --> 316.83
staging_process_max_fds --> 1024.0
"""[1:],
    }, {
        'about': 'match multiple samples: values-only output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'in_flight',
            '--format', 'values-only'],
        'text': helpers.example_text,
        'want_output': '7.0\n0.0\n',
    }, {
        'about': 'match specific sample: JSON output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'req.*in_flight',
            '--format', 'json'],
        'text': helpers.example_text,
        'want_output': """
[
    {
        "name": "jujushell_requests_in_flight",
        "tags": {},
        "value": 0.0
    }
]
"""[1:],
    }, {
        'about': 'match specific sample: values-only output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'jujushell_containers_duration_sum',
            '--format', 'values-only'],
        'text': helpers.example_text,
        'want_output': '27.648935921\n',
    }, {
        'about': 'match no samples: JSON output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'no such',
            '--format', 'points'],
        'text': helpers.example_text,
        'want_output': '[]\n',
    }, {
        'about': 'all samples: no output',
        'args': ['https://1.2.3.4/metrics', '--format', 'none'],
        'text': helpers.example_text,
    }, {
        'about': 'all samples to InfluxDB',
        'args': [
            'https://1.2.3.4/metrics',
            'influxdb://who:tardis@gallifrey:4242/skaro',
            '--format', 'none'],
        'want_influx_args': {
            'username': 'who',
            'password': 'tardis',
            'host': 'gallifrey',
            'port': 4242,
            'database': 'skaro',
        },
        'want_points': ({
            'measurement': 'jujushell_containers_duration_bucket',
            'time': 'right now',
            'fields': {'value': 2.0},
            'tags': {'le': '5', 'operation': 'create-container'},
        }, {
            'measurement': 'jujushell_containers_duration_bucket',
            'time': 'right now',
            'fields': {'value': 6.0},
            'tags': {'le': '10', 'operation': 'create-container'},
        }, {
            'measurement': 'jujushell_containers_duration_bucket',
            'time': 'right now',
            'fields': {'value': 7.0},
            'tags': {'le': '+Inf', 'operation': 'create-container'},
        }, {
            'measurement': 'jujushell_containers_duration_sum',
            'time': 'right now',
            'fields': {'value': 27.648935921},
            'tags': {'operation': 'create-container'},
        }, {
            'measurement': 'jujushell_containers_duration_count',
            'time': 'right now',
            'fields': {'value': 7.0},
            'tags': {'operation': 'create-container'},
        }, {
            'measurement': 'jujushell_containers_in_flight',
            'time': 'right now',
            'fields': {'value': 7.0},
            'tags': {},
        }, {
            'measurement': 'jujushell_errors_count',
            'time': 'right now',
            'fields': {'value': 5.0},
            'tags': {'message': 'cannot authenticate user'},
        }, {
            'measurement': 'jujushell_requests_count',
            'time': 'right now',
            'fields': {'value': 33.0},
            'tags': {'code': '200'},
        }, {
            'measurement': 'jujushell_requests_in_flight',
            'time': 'right now',
            'fields': {'value': 0.0},
            'tags': {},
        }, {
            'measurement': 'process_cpu_seconds_total',
            'time': 'right now',
            'fields': {'value': 316.83}, 'tags': {},
        }, {
            'measurement': 'process_max_fds',
            'time': 'right now',
            'fields': {'value': 1024.0},
            'tags': {},
        }),
        'text': helpers.example_text,
    }, {
        'about': 'some samples to InfluxDB',
        'args': [
            'https://1.2.3.4/metrics',
            'influxdb://amy:rory@earth/db',
            '--format', 'none',
            '-m', 'in_flight'],
        'want_influx_args': {
            'username': 'amy',
            'password': 'rory',
            'host': 'earth',
            'port': 8086,
            'database': 'db',
        },
        'want_points': ({
            'measurement': 'jujushell_containers_in_flight',
            'time': 'right now',
            'fields': {'value': 7.0},
            'tags': {},
        }, {
            'measurement': 'jujushell_requests_in_flight',
            'time': 'right now',
            'fields': {'value': 0.0},
            'tags': {},
        }),
        'text': helpers.example_text,
    }, {
        'about': 'no samples to InfluxDB',
        'args': [
            'https://1.2.3.4/metrics',
            'influxdb://who:tardis@gallifrey:8086/skaro',
            '--format', 'none',
            '-m', 'no such'],
        'text': helpers.example_text,
    }, {
        'about': 'skip TLS cert verification',
        'args': [
            'https://1.2.3.4/metrics',
            '--no-verify',
            '--format', 'none',
            '-m', 'no such'],
        'text': helpers.example_text,
    }]

    def test_success(self):
        # The fsteal command is successfully executed.
        for test in self.success_tests:
            with self.subTest(test['about']):
                self.success(
                    test.get('args', []),
                    test.get('text', ''),
                    test.get('want_output', ''),
                    test.get('want_influx_args', {}),
                    test.get('want_points', []),
                )

    failure_tests = [{
        'about': 'invalid InfluxDB connection string',
        'args': ['https://1.2.3.4/metrics', 'influxdb://bad-wolf'],
        'text': helpers.example_text,
        'want_error': "invalid InfluxDB connection string 'bad-wolf'",
    }, {
        'about': 'error while writing to InfluxDB',
        'args': ['https://1.2.3.4/metrics', 'influxdb://u:p@host/db'],
        'text': helpers.example_text,
        'influx_error': 'bad wolf',
        'want_error': 'cannot write to InfluxDB: bad wolf',
    }, {
        'about': 'error while reading from Prometheus',
        'args': ['https://1.2.3.4/metrics', 'influxdb://u:p@host/db'],
        'text': helpers.example_text,
        'urlopen_error': 'bad wolf',
        'want_error': 'cannot read from Prometheus endpoint: bad wolf',
    }]

    def test_failure(self):
        # The application exists in case of errors.
        for test in self.failure_tests:
            with self.subTest(test['about']):
                self.failure(
                    test.get('args', []),
                    test.get('text', ''),
                    test.get('urlopen_error', None),
                    test.get('influx_error', None),
                    test.get('want_error', ''),
                )

    def success(self, args, text, want_output, want_influx_args, want_points):
        with self.patch_urlopen(text) as mock_urlopen:
            with self.patch_influx() as (mock_client, mock_write):
                with mock.patch('sys.stdout', new=StringIO()) as mock_stdout:
                    with mock.patch('datetime.datetime') as mock_datetime:
                        mock_datetime.utcnow = lambda: 'right now'
                        firestealer.fsteal(args)
        if '--no-verify' in args:
            self.assertEqual(
                mock_urlopen.call_count, 1, mock_urlopen.mock_calls)
            urlopen_args, urlopen_kwargs = mock_urlopen.call_args
            self.assertEqual(urlopen_args[0], args[0])
            context = urlopen_kwargs['context']
            self.assertFalse(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_NONE)
        else:
            mock_urlopen.assert_called_once_with(args[0], context=None)
        self.assertEqual(mock_stdout.getvalue(), want_output)
        if want_points:
            mock_client.assert_called_once_with(**want_influx_args)
            mock_write.assert_called_once_with(want_points)
        else:
            self.assertEqual(mock_client.call_count, 0, mock_client.mock_calls)
            self.assertEqual(mock_write.call_count, 0, mock_write.mock_calls)

    def failure(self, args, text, urlopen_error, influx_error, want_error):
        with self.patch_urlopen(text, error=urlopen_error):
            with self.patch_influx() as (mock_client, mock_write):
                if influx_error:
                    mock_write.side_effect = ValueError(influx_error)
                with mock.patch('sys.exit') as mock_exit:
                    firestealer.fsteal(args)
        self.assertEqual(mock_exit.call_count, 1)
        got_error = str(mock_exit.call_args[0][0])
        self.assertEqual(got_error, want_error)

    def patch_urlopen(self, text, error=None):
        """Patch urllib.request.urlopen so that it returns the given text.

        If an error message is passed, simulate that an exception is raised
        in the process with the given error.
        """
        cm = mock.MagicMock()
        if error:
            cm.getcode.return_value = 400
            cm.read.side_effect = ValueError(error)
        else:
            cm.getcode.return_value = 200
            cm.read.return_value = text.encode('utf-8')
        cm.__enter__.return_value = cm
        return mock.patch('urllib.request.urlopen', return_value=cm)

    @contextmanager
    def patch_influx(self):
        with mock.patch('firestealer._influx.InfluxDBClient') as mock_client:
            mock_write = mock_client().write_points
            mock_client.reset_mock()
            yield mock_client, mock_write


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


class TestTextToSamples(TestCase):

    tests = [{
        'about': 'no samples',
    }, {
        'about': 'all samples',
        'text': helpers.example_text,
        'want_samples': (
            firestealer.Sample(
                name='jujushell_containers_duration_bucket',
                tags={'le': '5', 'operation': 'create-container'},
                value=2.0),
            firestealer.Sample(
                name='jujushell_containers_duration_bucket',
                tags={'le': '10', 'operation': 'create-container'},
                value=6.0),
            firestealer.Sample(
                name='jujushell_containers_duration_bucket',
                tags={'le': '+Inf', 'operation': 'create-container'},
                value=7.0),
            firestealer.Sample(
                name='jujushell_containers_duration_sum',
                tags={'operation': 'create-container'},
                value=27.648935921),
            firestealer.Sample(
                name='jujushell_containers_duration_count',
                tags={'operation': 'create-container'},
                value=7.0),
            firestealer.Sample(
                name='jujushell_requests_duration',
                tags={'quantile': '0.99', 'code': '200'},
                value=math.nan),
            firestealer.Sample(
                name='jujushell_containers_in_flight',
                tags={},
                value=7.0),
            firestealer.Sample(
                name='jujushell_errors_count',
                tags={'message': 'cannot authenticate user'},
                value=5.0),
            firestealer.Sample(
                name='jujushell_requests_count',
                tags={'code': '200'},
                value=33.0),
            firestealer.Sample(
                name='jujushell_requests_in_flight',
                tags={},
                value=0.0),
            firestealer.Sample(
                name='process_cpu_seconds_total',
                tags={},
                value=316.83),
            firestealer.Sample(
                name='process_max_fds',
                tags={},
                value=1024.0),
        ),
    }, {
        'about': 'regex: process samples',
        'text': helpers.example_text,
        'regex': '^process',
        'want_samples': (
            firestealer.Sample(
                name='process_cpu_seconds_total',
                tags={},
                value=316.83),
            firestealer.Sample(
                name='process_max_fds',
                tags={},
                value=1024.0),
        ),
    }, {
        'about': 'regex: no samples',
        'text': helpers.example_text,
        'regex': 'no such',
    }, {
        'about': 'regex: complex expression',
        'text': helpers.example_text,
        'regex': 'in_flight|errors',
        'want_samples': (
            firestealer.Sample(
                name='jujushell_containers_in_flight',
                tags={},
                value=7.0),
            firestealer.Sample(
                name='jujushell_errors_count',
                tags={'message': 'cannot authenticate user'},
                value=5.0),
            firestealer.Sample(
                name='jujushell_requests_in_flight',
                tags={},
                value=0.0),
        ),
    }, {
        'about': 'regex: specific sample',
        'text': helpers.example_text,
        'regex': 'jujushell_containers_duration_count',
        'want_samples': (
            firestealer.Sample(
                name='jujushell_containers_duration_count',
                tags={'operation': 'create-container'},
                value=7.0),
        ),
    }, {
        'about': 'regex and prefix: multiple results',
        'text': helpers.example_text,
        'regex': 'count$',
        'prefix': 'staging-',
        'want_samples': (
            firestealer.Sample(
                name='staging-jujushell_containers_duration_count',
                tags={'operation': 'create-container'},
                value=7.0),
            firestealer.Sample(
                name='staging-jujushell_errors_count',
                tags={'message': 'cannot authenticate user'},
                value=5.0),
            firestealer.Sample(
                name='staging-jujushell_requests_count',
                tags={'code': '200'},
                value=33.0),
        ),
    }, {
        'about': 'regex and prefix: specific result',
        'text': helpers.example_text,
        'regex': 'jujushell_requests_in_flight',
        'prefix': 'prod_',
        'want_samples': (
            firestealer.Sample(
                name='prod_jujushell_requests_in_flight',
                tags={},
                value=0.0),
        ),
    }]

    def test_samples(self):
        # Samples are created starting from a text content.
        for test in self.tests:
            with self.subTest(test['about']):
                self.check_samples(
                    test.get('text', ''),
                    test.get('regex', ''),
                    test.get('prefix', ''),
                    test.get('want_samples', ()),
                )

    def check_samples(self, text, regex, prefix, want_samples):
        # Check to see if a NaN sample is expected.
        want_nan_sample, want_samples = self.pop_nan_sample(want_samples)
        # Retrieve the samples.
        got_samples = firestealer.text_to_samples(
            text, regex=regex, prefix=prefix)
        # Check to see if a NaN sample has been retrieved.
        got_nan_sample, got_samples = self.pop_nan_sample(got_samples)
        if want_nan_sample is None:
            self.assertIsNone(got_nan_sample)
        else:
            self.assertEqual(got_nan_sample.name, want_nan_sample.name)
            self.assertEqual(got_nan_sample.tags, want_nan_sample.tags)
        self.assertEqual(got_samples, want_samples)

    def pop_nan_sample(self, samples):
        """Check if the given samples include a NaN sample.

        Return the NaN sample (or None) and the remaining samples.
        """
        valid_samples, nan_sample = [], None
        for sample in samples:
            if math.isnan(sample.value):
                self.assertIsNone(nan_sample, 'more than one NaN samples')
                nan_sample = sample
                continue
            valid_samples.append(sample)
        return nan_sample, tuple(valid_samples)
