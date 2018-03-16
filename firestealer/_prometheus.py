# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Prometheus metrics retriever and parser."""

from collections import namedtuple
import re

from prometheus_client.parser import text_string_to_metric_families


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


# A sample represents a sigle Prometheus key/value measurement.
Sample = namedtuple('Sample', ['name', 'tags', 'value'])
