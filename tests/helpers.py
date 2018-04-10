# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Firestealer test helpers."""

from contextlib import contextmanager
import math
import ssl
from unittest import mock


# Define some example Prometheus data for testing.
example_text = """
# HELP jujushell_containers_duration time spent doing container operations
# TYPE jujushell_containers_duration histogram
jujushell_containers_duration_bucket{operation="create-container",le="5"} 2
jujushell_containers_duration_bucket{operation="create-container",le="10"} 6
jujushell_containers_duration_bucket{operation="create-container",le="+Inf"} 7
jujushell_containers_duration_sum{operation="create-container"} 27.648935921
jujushell_containers_duration_count{operation="create-container"} 7
# HELP jujushell_containers_in_flight the number of current containers
# TYPE jujushell_containers_in_flight gauge
jujushell_containers_in_flight 7
# HELP jujushell_errors_count the number of encountered errors
# TYPE jujushell_errors_count counter
jujushell_errors_count{message="cannot authenticate user"} 5
# HELP jujushell_requests_count the total count of requests
# TYPE jujushell_requests_count counter
jujushell_requests_count{code="200"} 33
# HELP jujushell_requests_duration time spent in requests
# TYPE jujushell_requests_duration summary
jujushell_requests_duration{code="200",quantile="0.99"} NaN
# HELP jujushell_requests_in_flight the number of requests currently in flight
# TYPE jujushell_requests_in_flight gauge
jujushell_requests_in_flight 0
# HELP process_cpu_seconds_total total user and system CPU time
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 316.83
# HELP process_max_fds maximum number of open file descriptors
# TYPE process_max_fds gauge
process_max_fds 1024
"""


@contextmanager
def patch_influx():
    """Patch the InfluxDB client and its write_points method."""
    with mock.patch('firestealer._influx.InfluxDBClient') as mock_client:
        mock_write = mock_client().write_points
        mock_client.reset_mock()
        yield mock_client, mock_write


def patch_urlopen(text, error=None):
    """Patch urllib.request.urlopen so that it returns the given text.

    If an error message is passed, simulate that an exception is raised in the
    process with the given error.
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


def check_urlopen(test, mock_urlopen, expected_url, noverify=False):
    """Check that the urlopen mock has been called once with the given URL."""
    verify = not noverify
    if verify:
        mock_urlopen.assert_called_once_with(expected_url, context=None)
        return
    # Certificate verification is disabled.
    test.assertEqual(mock_urlopen.call_count, 1, mock_urlopen.mock_calls)
    urlopen_args, urlopen_kwargs = mock_urlopen.call_args
    test.assertEqual(urlopen_args[0], expected_url)
    context = urlopen_kwargs['context']
    test.assertFalse(context.check_hostname)
    test.assertEqual(context.verify_mode, ssl.CERT_NONE)


@contextmanager
def maybe_raises(exception):
    """Assume the code in the block may or may not raise an exception.

    Report wether an exception with the given type has been raised.
    Raise an exception if one exception is raised but not the one provided.
    """
    ctx = type('Context', (), {'exc': None})()
    try:
        yield ctx
    except exception as err:
        ctx.exc = err


def assert_samples(test, got_samples, want_samples):
    """Check that we got the samples we want. Handle NaN samples."""
    want_nan_sample, want_samples = _pop_nan_sample(want_samples)
    got_nan_sample, got_samples = _pop_nan_sample(got_samples)
    if want_nan_sample is None:
        test.assertIsNone(got_nan_sample)
    else:
        test.assertEqual(got_nan_sample.name, want_nan_sample.name)
        test.assertEqual(got_nan_sample.tags, want_nan_sample.tags)
    test.assertEqual(got_samples, want_samples)


def _pop_nan_sample(samples):
    """Scan the given samples looking for a single NaN sample.

    Return the NaN sample (or None) and the remaining samples.
    """
    valid_samples, nan_sample = [], None
    for sample in samples:
        if math.isnan(sample.value):
            if nan_sample is not None:
                raise ValueError('more than one NaN samples found')
            nan_sample = sample
            continue
        valid_samples.append(sample)
    return nan_sample, tuple(valid_samples)
