# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

import math
from unittest import TestCase

from . import helpers
import firestealer


class TestRetrieveSamples(TestCase):

    tests = [{
        'about': 'all samples',
        'text': helpers.example_text,
    }, {
        'about': 'no samples',
        'text': '',
    }, {
        'about': 'regex',
        'regex': '^process',
        'text': helpers.example_text,
    }, {
        'about': 'prefix',
        'prefix': 'prefix_',
        'text': helpers.example_text,
    }, {
        'about': 'regex and prefix',
        'regex': 'flight',
        'prefix': 'test-',
        'noverify': True,
        'text': helpers.example_text,
    }, {
        'about': 'noverify',
        'noverify': True,
        'text': helpers.example_text,
    }, {
        'about': 'error',
        'error': 'bad wolf',
        'want_error': 'cannot read from Prometheus endpoint: bad wolf',
    }]

    def test_retrieve_samples(self):
        # Samples can be successfully retrieved.
        for test in self.tests:
            with self.subTest(test['about']):
                self.retrieve(
                    test.get('regex', ''),
                    test.get('prefix', ''),
                    test.get('noverify', False),
                    test.get('text', ''),
                    test.get('error', None),
                    test.get('want_error', ''),
                )

    def retrieve(self, regex, prefix, noverify, text, error, want_error):
        url = 'https://example.com/metrics'
        with helpers.patch_urlopen(text, error=error) as mock_urlopen:
            with helpers.maybe_raises(firestealer.PrometheusError) as ctx:
                got_samples = firestealer.retrieve_samples(
                    url, regex=regex, prefix=prefix, noverify=noverify)
        helpers.check_urlopen(self, mock_urlopen, url, noverify=noverify)
        if want_error:
            self.assertEqual(str(ctx.exc), want_error)
            return
        self.assertIsNone(ctx.exc)
        want_samples = firestealer.text_to_samples(
            text, regex=regex, prefix=prefix)
        helpers.assert_samples(self, got_samples, want_samples)


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
        got_samples = firestealer.text_to_samples(
            text, regex=regex, prefix=prefix)
        helpers.assert_samples(self, got_samples, want_samples)
