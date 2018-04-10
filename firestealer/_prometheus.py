# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Prometheus metrics retriever and parser."""

from collections import namedtuple
import re
import ssl
from urllib import request

from prometheus_client.parser import text_string_to_metric_families

from . import _exceptions


def text_to_samples(text, regex='', prefix=''):
    """Parse the given metrics text and return a sequence of samples.

    Only return samples whose name matches the given regex.
    If a prefix is provided, include that in the resultimg sample names.
    """
    match = re.compile(regex).search
    samples = []
    for family in text_string_to_metric_families(text):
        samples.extend(
            Sample(prefix + name, tags, value)
            for name, tags, value in family.samples if match(name)
        )
    return tuple(samples)


def retrieve_samples(url, regex='', prefix='', noverify=False):
    """Retrieve and return samples from the given Prometheus URL.

    Raise a firestealer.PrometheusError if the samples cannot be retrieved.

    Only return samples whose name matches the given regex.
    If a prefix is provided, include that in the resultimg sample names.
    If noverify is True, then do not validate URL certificates.
    """
    context = None
    if noverify:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    try:
        with request.urlopen(url, context=context) as response:
            text = response.read().decode('utf-8')
    except Exception as err:
        raise _exceptions.PrometheusError(
            'cannot read from Prometheus endpoint: {}'.format(err))
    return text_to_samples(text, regex=regex, prefix=prefix)


# A sample represents a sigle Prometheus key/value measurement.
Sample = namedtuple('Sample', ['name', 'tags', 'value'])
