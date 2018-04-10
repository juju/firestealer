firestealer
===========

Parse and filter metrics from `Prometheus <https://prometheus.io/>`_ endpoints
so that they can be visualized, stored into
`InfluxDB <https://www.influxdata.com/time-series-platform/influxdb/>`_, or used
as `Juju charm <https://jujucharms.com/>`_ metrics.

Installation
------------

Run `pip install firestealer`. This will make the `fsteal` command available.

CLI
---
Print JSON formatted samples from a Prometehus endpoint::

    $ fsteal http://localhost:8000/metrics

Filter metrics using a regular expression against the sample name::

    $ fsteal http://localhost:8000/metrics -m '^myservice(Downloads|Uploads)'

Store samples into InfluxDB::

    $ fsteal localhost:8000/metrics influxdb://user:passwd@10.0.0.1:8086/mydb

Store a subset of samples into InfluxDB::

    $ fsteal localhost:8000/metrics influxdb://user:passwd@10.0.0.1:8086/mydb -m '^myservice'

In the example above the InfluxDB connection info is provided using a
`influxdb://$user:$passwd@$host:$port/$database` connection string.

Only print specific metrics values (useful when executing fsteal in order to
retrieve charm metrics)::

    $ fsteal localhost:8000/metrics a-single-specific-key --format values-only

API Usage
---------

An API is exposed so that firestealer can be used as a library from Python
applications. For instance, a charm could propagate metrics from Prometheus
to Juju with the following snippet placed in the
`collect-metrics <https://jujucharms.com/docs/2.3/reference-charm-hooks#collect-metrics>`_
hook::

    from firestealer import (
        add_metrics,
        retrieve_metrics,
    )

    url = 'https://localhost:8000/metrics'
    with open('metrics.yaml') as f:
        metrics = yaml.safe_load(f)
    samples = retrieve_metrics(url, metrics, noverify=True)
    add_metrics(samples)

Similarly, to write relevant samples to InfluxDB, the following snippet can be
used::

    from firestealer import (
        retrieve_metrics,
        write_to_influx,
    )

    url = 'https://localhost:8000/metrics'
    with open('metrics.yaml') as f:
        metrics = yaml.safe_load(f)
    samples = retrieve_metrics(url, metrics)
    write_to_influx('user:passwd@1.2.3.4/dbname', samples)

API Reference
-------------

**add_metrics(samples)**
    Add the given samples as metrics to Juju.

    This function assumes an add-metric executable to be present in the PATH.

**retrieve_metrics(url, metrics, noverify=False)**
    Retrieve samples for the given metrics from the given Prometheus URL.

    Raise a firestealer.PrometheusError if the samples cannot be retrieved.

    Only return samples whose name is included in the given metrics object,
    which is a decoded metrics.yaml content. Samples are renamed based on the
    metrics provided.
    If noverify is True, then do not validate URL certificates.

**retrieve_samples(url, regex='', prefix='', noverify=False)**
    Retrieve and return samples from the given Prometheus URL.

    Raise a firestealer.PrometheusError if the samples cannot be retrieved.

    Only return samples whose name matches the given regex.
    If a prefix is provided, include that in the resultimg sample names.
    If noverify is True, then do not validate URL certificates.

**samples_to_points(samples)**
    Convert samples to InfluxDB points.

    Only samples with an actual value are included in the resulting list.

**text_to_samples(text, regex='', prefix='')**
    Parse the given metrics text and return a sequence of samples.

    Only return samples whose name matches the given regex.
    If a prefix is provided, include that in the resultimg sample names.

**write_to_influx(conn_string, samples)**
    Write the given samples to the InfluxDB at the given connection string.

    The connection string is in "$user:$passwd@$host:$port/$database" form.
    Raise a firestealer.InfluxError if the connection string is not well formed
    or when it is not possible to communicate with InfluxDB.

**Sample** = namedtuple('Sample', ['name', 'tags', 'value'])
    A sample represents a sigle Prometheus key/value measurement.
