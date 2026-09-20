# Solution: Exercise 6 - Real-Time Monitoring and Alerting (Prometheus + Grafana)

Goal: monitor a quick-commerce delivery service with a Python metrics exporter, Prometheus (scraping and alert rules) and a Grafana dashboard.

Environment: Windows 11, Docker Desktop, Python 3.x with `prometheus-client`, Prometheus (`prom/prometheus`), Grafana 13.2.1.

## Files (`delivery_monitoring/`)

| File | Purpose |
|------|---------|
| `delivery_metrics.py` | Exposes `/metrics` on port 8000: gauges `pending_deliveries`, `on_the_way_deliveries`, `total_deliveries` and summary `delivery_time_seconds`; updates every second |
| `prometheus.yml` | Scrape jobs (Prometheus itself and `delivery_service`) and the alert rules file |
| `alert_rules.yml` | `HighPendingDeliveries` and `HighAverageDeliveryTime` |
| `grafana_dashboard.json` | Dashboard with the four required panels |
| `Jenkinsfile` | Pipeline that validates Docker and starts the app, Prometheus and Grafana |

## Steps and results

### 1. Metrics exporter

```bash
pip install prometheus-client
python delivery_metrics.py
curl http://localhost:8000/metrics
```

```
pending_deliveries 3.0
on_the_way_deliveries 14.0
total_deliveries 13.0
delivery_time_seconds_count 6.0
delivery_time_seconds_sum 147.77
```

### 2. Prometheus

```bash
docker network create monitoring-net
docker run -d --name prometheus --network monitoring-net -p 9090:9090 \
  --add-host=host.docker.internal:host-gateway \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  -v ./alert_rules.yml:/etc/prometheus/alert_rules.yml prom/prometheus
```

Both targets are `up` at http://localhost:9090/targets:

```
delivery_service  http://host.docker.internal:8000/metrics  up
prometheus        http://localhost:9090/metrics              up
```

Differences from the exercise text: `--network=host` does not expose ports on Docker Desktop for Windows, so ports are published with `-p`, and the exporter (running on the host) is reached as `host.docker.internal`. On Linux/WSL use `172.17.0.1`.

### 3. Alert rules

| Alert | Expression | For |
|-------|------------|-----|
| `HighPendingDeliveries` | `pending_deliveries > 10` | 15s |
| `HighAverageDeliveryTime` | `rate(delivery_time_seconds_sum[1m]) / rate(delivery_time_seconds_count[1m]) > 30` | 15s |

### 4. Grafana

```bash
docker run -d --name grafana --network monitoring-net -p 3000:3000 grafana/grafana
```

Logged in at http://localhost:3000 as `admin` / `admin` (the default credentials, which Grafana prompts you to change). A Prometheus data source was added with URL `http://prometheus:9090`. Because both containers share `monitoring-net`, the container name works; the exercise's `http://172.17.0.1:9090` is the Linux equivalent.

The data source health check returns "Successfully queried the Prometheus API", and a query through Grafana returned live `pending_deliveries` data.

The dashboard "Delivery Operations" (imported from `grafana_dashboard.json`, refresh 5s) has four panels:

1. Total Deliveries (stat)
2. Pending Deliveries (time series)
3. On-the-Way Deliveries (time series)
4. Average Delivery Time (gauge, red above 30s)

### 5. Testing the alerts

With `pending = random.randint(50, 100)` in the exporter and a restart:

```
HighPendingDeliveries    state=firing    value=59    severity=warning
HighAverageDeliveryTime  state=inactive  health=ok
```

`HighPendingDeliveries` fires after the 15s `for` window. `HighAverageDeliveryTime` stays inactive because the simulated times are 10-40s (average about 25s).

### 6. Jenkins (not run)

The `Jenkinsfile` is written (validate Docker, copy config files, run the metrics app, start Prometheus and Grafana) but was not executed. Running it needs the Jenkins setup wizard (unlock with the initial admin password, install plugins, create a pipeline job) and Docker access from inside the Jenkins container, which was out of scope here.

## Notes

- The exercise names the rules file both `alerts_rules.yml` and `alert_rules.yml`; `alert_rules.yml` is used throughout, as in the `docker run` command.
- The exercise text did not include the code, so the exporter, configs and dashboard were written from its description.

## Cleanup

```bash
docker rm -f prometheus grafana
docker network rm monitoring-net
```
Stop the exporter with Ctrl+C.
