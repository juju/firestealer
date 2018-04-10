# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Application custom exceptions."""


class FirestealerError(Exception):
    """An error occurred while running firestealer."""


class InfluxError(FirestealerError):
    """An error occurred while communicating with InfluxDB."""


class PrometheusError(FirestealerError):
    """An error occurred while communicating with Prometheus."""
