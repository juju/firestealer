# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Juju charm helpers."""

import subprocess

from . import _prometheus


def format_charm(samples):
    """Format samples so that they can be used in a collect-metrics hook."""
    if not samples:
        return ''
    return ' '.join(_metrics(samples))


def add_metrics(samples):
    """Add the given samples as metrics to Juju.

    This function assumes an add-metric executable to be present in the PATH.
    """
    if samples:
        subprocess.check_call(_metrics(samples))


def retrieve_metrics(url, metrics, noverify=False):
    """Retrieve samples for the given metrics from the given Prometheus URL.

    Raise a firestealer.PrometheusError if the samples cannot be retrieved.

    Only return samples whose name is included in the given metrics object,
    which is a decoded metrics.yaml content. Samples are renamed based on the
    metrics provided.
    If noverify is True, then do not validate URL certificates.
    """
    names = tuple(sorted(metrics.get('metrics', {})))
    if not names:
        return ()
    # Retrieve samples from Prometheus.
    regex = '|'.join(names)
    samples = _prometheus.retrieve_samples(url, regex=regex, noverify=noverify)
    # Rename samples based on the provided metrics.
    samples, results = list(samples), []
    Sample = _prometheus.Sample
    for name in names:
        for sample in samples:
            if name in sample.name:
                results.append(Sample(name, sample.tags, sample.value))
                samples.remove(sample)
    return tuple(results)


def _metrics(samples):
    return ['add-metric'] + ['{}={}'.format(s.name, s.value) for s in samples]
