# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Handlers for connecting and executing queries in InfluxDB."""

import datetime
import math
import re

from influxdb import InfluxDBClient

from . import _exceptions


def write(conn_string, samples):
    """Write the given samples to the InfluxDB at the given connection string.

    The connection string is in "$user:$passwd@$host:$port/$database" form.
    """
    match = _exp.match(conn_string)
    if match is None:
        raise _exceptions.AppError(
            'invalid InfluxDB connection string {!r}'.format(conn_string))
    group = match.groupdict()
    info = {
        'username': group['username'],
        'password': group['password'],
        'host': group['ipv6host'] or group['ipv4host'],
        'port': int(group['port'] or 8086),
        'database': group['database'],
    }
    points = samples_to_points(samples)
    try:
        client = InfluxDBClient(**info)
        client.write_points(points)
    except Exception as err:
        raise _exceptions.AppError('cannot write to InfluxDB: {}'.format(err))


def samples_to_points(samples):
    """Convert samples to InfluxDB points.

    Only samples with an actual value are included in the resulting list.
    """
    def hasvalue(sample):
        try:
            return not math.isnan(sample.value)
        except TypeError:
            # The value is not a number, assume it is good to go.
            return True

    now = str(datetime.datetime.utcnow())
    return tuple({
        "measurement": sample.name,
        "tags": sample.tags,
        "time": now,
        "fields": {"value": sample.value}
    } for sample in filter(hasvalue, samples))


# Define a regular expression for parsing connection strings.
_exp = re.compile(r"""
    (?P<username>[^:/]+)
    (?::(?P<password>.*))?
    @
    (?:
        \[(?P<ipv6host>[^/]+)\] |
        (?P<ipv4host>[^/:]+)
    )
    (?::(?P<port>\d[^/]+))?
    /
    (?P<database>.+)
""", re.X)
