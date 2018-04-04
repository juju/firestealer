firestealer
===========

Parse and filter metrics from `Prometheus <https://prometheus.io/>`_ endpoints
so that they can be visualized, stored into
`InfluxDB <https://www.influxdata.com/time-series-platform/influxdb/>`_, or used
as `Juju charm <https://jujucharms.com/>`_ metrics.

Installation
------------

Run `pip install firestealer`. This will make the `fsteal` command available.

Usage
-----
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

API
---

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
