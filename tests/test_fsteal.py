# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

from contextlib import contextmanager
from io import StringIO
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
        'about': 'match multiple samples: charm output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'in_flight',
            '--format', 'charm'],
        'text': helpers.example_text,
        'want_output': (
            'add-metric '
            'jujushell_containers_in_flight=7.0 '
            'jujushell_requests_in_flight=0.0\n'),
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
        'about': 'match specific sample: charm output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'process_max_fds',
            '--format', 'charm'],
        'text': helpers.example_text,
        'want_output': 'add-metric process_max_fds=1024.0\n',
    }, {
        'about': 'match no samples: JSON output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'no such',
            '--format', 'json'],
        'text': helpers.example_text,
        'want_output': '[]\n',
    }, {
        'about': 'match no samples: charm output',
        'args': [
            'http://4.3.2.1/metrics',
            '-m', 'no such',
            '--format', 'charm'],
        'text': helpers.example_text,
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
        with helpers.patch_urlopen(text) as mock_urlopen:
            with self.patch_influx() as (mock_client, mock_write):
                with mock.patch('sys.stdout', new=StringIO()) as mock_stdout:
                    with mock.patch('datetime.datetime') as mock_datetime:
                        mock_datetime.utcnow = lambda: 'right now'
                        firestealer.fsteal(args)
        helpers.check_urlopen(
            self, mock_urlopen, args[0], noverify='--no-verify' in args)
        self.assertEqual(mock_stdout.getvalue(), want_output)
        if want_points:
            mock_client.assert_called_once_with(**want_influx_args)
            mock_write.assert_called_once_with(want_points)
        else:
            self.assertEqual(mock_client.call_count, 0, mock_client.mock_calls)
            self.assertEqual(mock_write.call_count, 0, mock_write.mock_calls)

    def failure(self, args, text, urlopen_error, influx_error, want_error):
        with helpers.patch_urlopen(text, error=urlopen_error):
            with self.patch_influx() as (mock_client, mock_write):
                if influx_error:
                    mock_write.side_effect = ValueError(influx_error)
                with mock.patch('sys.exit') as mock_exit:
                    firestealer.fsteal(args)
        self.assertEqual(mock_exit.call_count, 1)
        got_error = str(mock_exit.call_args[0][0])
        self.assertEqual(got_error, want_error)

    @contextmanager
    def patch_influx(self):
        with mock.patch('firestealer._influx.InfluxDBClient') as mock_client:
            mock_write = mock_client().write_points
            mock_client.reset_mock()
            yield mock_client, mock_write
