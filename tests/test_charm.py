# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

from unittest import (
    mock,
    TestCase,
)

from . import helpers
import firestealer


@mock.patch('subprocess.check_call')
class TestAddMetrics(TestCase):

    def test_no_samples(self, mock_call):
        # Without samples, no metrics are added.
        firestealer.add_metrics([])
        self.assertEqual(mock_call.call_count, 0)

    def test_with_samples(self, mock_call):
        # When samples are present, the add-metric command is executed.
        samples = [
            firestealer.Sample('s1', {'tag1': 'value1'}, 42),
            firestealer.Sample('s2', {}, 47),
            firestealer.Sample('s3', {'true': True, 'false': False}, 1.0),
        ]
        firestealer.add_metrics(samples)
        mock_call.assert_called_once_with(
            ['add-metric', 's1=42', 's2=47', 's3=1.0'])


class TestRetrieveMetrics(TestCase):

    tests = [{
        'about': 'no metrics',
    }, {
        'about': 'specific metrics',
        'metrics': {'metrics': {'errors_count': {}}},
        'want_samples': (
            firestealer.Sample(
                name='errors_count',
                tags={'message': 'cannot authenticate user'},
                value=5.0),
        ),
    }, {
        'about': 'multiple metrics',
        'metrics': {'metrics': {
            'errors_count': {},
            'containers_in_flight': {},
            'process_max_fds': {},
        }},
        'want_samples': (
            firestealer.Sample(
                name='containers_in_flight',
                tags={},
                value=7.0),
            firestealer.Sample(
                name='errors_count',
                tags={'message': 'cannot authenticate user'},
                value=5.0),
            firestealer.Sample(
                name='process_max_fds',
                tags={},
                value=1024.0),
        ),
    }, {
        'about': 'error',
        'metrics': {'metrics': {'errors_count': {}}},
        'error': 'bad wolf',
        'want_error': 'cannot read from Prometheus endpoint: bad wolf',
    }]

    def test_retrieve_metrics(self):
        # Samples can be successfully retrieved.
        for test in self.tests:
            with self.subTest(test['about']):
                self.retrieve(
                    test.get('metrics', {}),
                    test.get('noverify', False),
                    test.get('error', None),
                    test.get('want_error', ''),
                    test.get('want_samples', ''),
                )

    def retrieve(self, metrics, noverify, error, want_error, want_samples):
        url = 'https://example.com/metrics'
        text = helpers.example_text
        with helpers.patch_urlopen(text, error=error) as mock_urlopen:
            with helpers.maybe_raises(firestealer.PrometheusError) as ctx:
                got_samples = firestealer.retrieve_metrics(
                    url, metrics, noverify=noverify)
        if metrics:
            helpers.check_urlopen(self, mock_urlopen, url, noverify=noverify)
        else:
            self.assertEqual(mock_urlopen.call_count, 0)
        if want_error:
            self.assertEqual(str(ctx.exc), want_error)
            return
        self.assertIsNone(ctx.exc)
        helpers.assert_samples(self, got_samples, want_samples)
