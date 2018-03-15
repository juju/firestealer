# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Prometheus metrics retriever and parser."""

from collections import namedtuple
import re
from urllib import request

from prometheus_client.parser import text_string_to_metric_families

from . import exceptions


def parse(url, regex, prefix):
    """Parse metrics from the given URL and return a sequence of samples.

    Only return samples whose name matches the given regex.
    If a prefix is provided, include that in the resultimg sample names.
    """
    match = re.compile(regex).search
    try:
        with request.urlopen(url) as response:
            content = response.read().decode('utf-8')
    except Exception as err:
        raise exceptions.AppError(
            'cannot read Prometheus endpoint: {}'.format(err))
    samples = []
    for family in text_string_to_metric_families(content):
        samples.extend(
            Sample(prefix+name, tags, value)
            for name, tags, value in family.samples if match(prefix+name)
        )
    return tuple(samples)


# A sample represents a sigle Prometheus key/value measurement.
Sample = namedtuple('Sample', ['name', 'tags', 'value'])
