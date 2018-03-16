# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Firestealer test helpers."""

# Define some example Prometheus data for testing.
example_text = """
# HELP jujushell_containers_duration time spent doing container operations
# TYPE jujushell_containers_duration histogram
jujushell_containers_duration_bucket{operation="create-container",le="5"} 2
jujushell_containers_duration_bucket{operation="create-container",le="10"} 6
jujushell_containers_duration_bucket{operation="create-container",le="+Inf"} 7
jujushell_containers_duration_sum{operation="create-container"} 27.648935921
jujushell_containers_duration_count{operation="create-container"} 7
# HELP jujushell_containers_in_flight the number of current containers
# TYPE jujushell_containers_in_flight gauge
jujushell_containers_in_flight 7
# HELP jujushell_errors_count the number of encountered errors
# TYPE jujushell_errors_count counter
jujushell_errors_count{message="cannot authenticate user"} 5
# HELP jujushell_requests_count the total count of requests
# TYPE jujushell_requests_count counter
jujushell_requests_count{code="200"} 33
# HELP jujushell_requests_duration time spent in requests
# TYPE jujushell_requests_duration summary
jujushell_requests_duration{code="200",quantile="0.99"} NaN
# HELP jujushell_requests_in_flight the number of requests currently in flight
# TYPE jujushell_requests_in_flight gauge
jujushell_requests_in_flight 0
# HELP process_cpu_seconds_total total user and system CPU time
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 316.83
# HELP process_max_fds maximum number of open file descriptors
# TYPE process_max_fds gauge
process_max_fds 1024
"""
