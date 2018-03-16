# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""A command line tool for parsing Prometheus metrics."""

import argparse
from collections import OrderedDict
from functools import partial
import json
from urllib import request

from . import (
    _exceptions,
    _influx,
    _prometheus,
)


def setup(args):
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('url', type=str, help='the Prometheus API endpoint')
    parser.add_argument(
        'target', type=str, default='', nargs='?', help="""
where to store samples:
- InfluxDB: connection info is provided using a
  "influxdb://$user:$passwd@$host:$port/$database"
  connection string"""[1:])
    format_choices = tuple(_format_choices.keys())
    parser.add_argument(
        '--format', choices=_format_choices, default=format_choices[0],
        help='how to format samples')
    parser.add_argument(
        '-m', '--match', type=str, default='', dest='regex',
        help='optional regex used to filter metrics')
    parser.add_argument(
        '--add-prefix', type=str, default='', dest='prefix',
        help='add a prefix to all sample names')
    ns = parser.parse_args(args)
    if ns.target and not ns.target.startswith(_INFLUX_SCHEMA):
        parser.error('invalid target {!r}'.format(ns.target))
        return
    return ns


def run(ns):
    """Run the application with the given parsed namespace."""
    try:
        with request.urlopen(ns.url) as response:
            text = response.read().decode('utf-8')
    except Exception as err:
        raise _exceptions.AppError(
            'cannot read from Prometheus endpoint: {}'.format(err))
    samples = _prometheus.text_to_samples(
        text, regex=ns.regex, prefix=ns.prefix)
    if samples and ns.target:
        # The only implemented target is InfluxDB currently.
        conn_string = ns.target[len(_INFLUX_SCHEMA):]
        _influx.write(conn_string, samples)
    format_func = _format_choices[ns.format]
    output = format_func(samples)
    if output:
        print(output)


def _format_text(samples):
    """Format samples as human readable text."""
    families = OrderedDict()
    for sample in samples:
        values = families.setdefault(sample.name, OrderedDict())
        tagitems = sorted(sample.tags.items())
        tags = ' '.join('{}={}'.format(k, v) for k, v in tagitems)
        values[tags] = sample.value
    text = []
    for family, values in families.items():
        value = values.pop('', None)
        if value is not None:
            family = '{} --> {}'.format(family, value)
        text.append(family)
        text.extend('  {} --> {}'.format(k, v) for k, v in values.items())
    return '\n'.join(text)


_dump = partial(json.dumps, indent=4)
# Define a map of format choices to format functions. A format function
# receives a sequence of samples and returns a string.
_format_choices = OrderedDict([
    ('text', _format_text),
    ('json', lambda samples: _dump([s._asdict() for s in samples])),
    ('values-only', lambda samples: '\n'.join(str(s.value) for s in samples)),
    ('points', lambda samples: _dump(_influx.samples_to_points(samples))),
    ('none', lambda _: ''),
])


_INFLUX_SCHEMA = 'influxdb://'
