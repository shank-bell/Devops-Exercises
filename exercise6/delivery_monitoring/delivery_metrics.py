import random
import time

from prometheus_client import Gauge, Summary, start_http_server

# Gauges track current values
pending_deliveries = Gauge("pending_deliveries", "Deliveries waiting to be picked up")
on_the_way_deliveries = Gauge("on_the_way_deliveries", "Deliveries currently on the way")
total_deliveries = Gauge("total_deliveries", "Total deliveries handled so far")

# Summary captures average delivery time (sum / count)
delivery_time = Summary("delivery_time_seconds", "Time taken to deliver an order")

if __name__ == "__main__":
    # Expose /metrics on port 8000 for Prometheus to scrape
    start_http_server(8000)
    print("Serving metrics on http://localhost:8000/metrics")

    total = 0
    while True:
        pending = random.randint(0, 10)  # for testing alerts use: random.randint(50, 100)
        on_the_way = random.randint(0, 20)
        total += random.randint(0, 3)

        pending_deliveries.set(pending)
        on_the_way_deliveries.set(on_the_way)
        total_deliveries.set(total)
        delivery_time.observe(random.uniform(10, 40))

        time.sleep(1)
