# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Handlers for connecting and executing queries in InfluxDB."""

from datetime import datetime
import math
import re

from influxdb import InfluxDBClient

from . import exceptions


def connect(conn_string):
    """Return an InfluxDB client getting info from the connection string.

    The connection string is in "$user:$passwd@$host:$port/$database" form.
    """
    match = _exp.match(conn_string)
    if match is None:
        raise exceptions.AppError(
            'invalid InfluxDB connection string {!r}'.format(conn_string))
    group = match.groupdict()
    info = {
        'username': group['username'],
        'password': group['password'],
        'host': group['ipv6host'] or group['ipv4host'],
        'port': group['port'] or 8086,
        'database': group['database'],
    }
    try:
        return InfluxDBClient(**info)
    except Exception as err:
        raise exceptions.AppError('cannot connect to InfluxDB: {}'.format(err))


def write(client, samples):
    """Push the given samples into the db using the given client.

    Only samples with an actual value are included.
    """
    def hasvalue(sample):
        try:
            return not math.isnan(sample.value)
        except TypeError:
            # The value is not a number, assume it is good to go.
            return True
    points = to_points(filter(hasvalue, samples))
    try:
        client.write_points(points)
    except Exception as err:
        raise exceptions.AppError('cannot write to InfluxDB: {}'.format(err))


def to_points(samples):
    """Convert samples to InfluxDB points."""
    now = str(datetime.utcnow())
    return tuple({
        "measurement": sample.name,
        "tags": sample.tags,
        "time": now,
        "fields": {"value": sample.value}
    } for sample in samples)


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
