# Solution: Exercise 4 - Docker Networking with Multiple Containers

Goal: run a three-container application (Flask API, MySQL, Redis) on a custom Docker bridge network, and show that containers find each other by name.

Environment: Windows 11, Docker Desktop (Docker 29.7).

## Files

| File | Purpose |
|------|---------|
| `app.py` | Flask API on port 5001; talks to MySQL and Redis by container name |
| `requirements.txt` | `flask`, `pymysql`, `cryptography`, `redis` |
| `Dockerfile` | Builds the `flask-api:1.0` image |

Endpoints: `/` (info), `/health` (checks MySQL and Redis), `/visit` (Redis counter), `/db` (inserts a row in MySQL and counts rows).

## Steps and actual output

### 1. Create a bridge network

```bash
docker network create --driver bridge my-bridge-net
```

### 2. Start MySQL and Redis on the network

```bash
docker run -d --name mysql --net=my-bridge-net -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.4
docker run -d --name redis --net=my-bridge-net redis:alpine
```

The exercise uses `mysql:latest`; `mysql:8.4` (the LTS release) is pinned so the result is repeatable. MySQL needs a root password to start.

### 3. Build and start the Flask API

```bash
docker build -t flask-api:1.0 .
docker run -d --name flask-api --net=my-bridge-net -p 5001:5001 flask-api:1.0
docker ps
```

```
NAMES       IMAGE           PORTS                      STATUS
flask-api   flask-api:1.0   0.0.0.0:5001->5001/tcp     Up
redis       redis:alpine    6379/tcp                   Up
mysql       mysql:8.4       3306/tcp, 33060/tcp        Up
```

Only the Flask API publishes a port (`-p 5001:5001`). MySQL and Redis are reachable only from inside the network.

### 4. Test the application

```
GET /health  -> {"mysql":"up","redis":"up"}
GET /visit   -> {"source":"redis@redis","visits":1}   (then 2, 3)
GET /db      -> {"rows_in_mysql":1,"source":"mysql@mysql"}   (then 2)
```

The API connects with the hostnames `mysql` and `redis`, not IP addresses.

### 5. Inspect the network

```bash
docker network inspect my-bridge-net
```

```
Subnet: 172.18.0.0/16
mysql      172.18.0.2/16
redis      172.18.0.3/16
flask-api  172.18.0.4/16
```

Name resolution from inside `flask-api`:

```
mysql -> 172.18.0.2
redis -> 172.18.0.3
```

### 6. Contrast with the default bridge

A container started without `--net` joins Docker's default bridge, which has no name-based DNS:

```bash
docker run --rm python:3.12-slim python -c "import socket; print(socket.gethostbyname('mysql'))"
```

```
FAILED: [Errno -2] Name or service not known
```

## Key points

- `--net=<network>` chooses which network a container joins at start.
- On a user-defined bridge network, Docker's embedded DNS resolves container names to IP addresses. The default bridge does not do this.
- A bridge network is a private subnet: containers talk to each other freely, but nothing is reachable from the host unless a port is published with `-p`.
- A host network removes that isolation: the container shares the host's network stack and needs no `-p`. It was not run here; on Docker Desktop for Windows it does not behave as on native Linux.
- Container IPs can change when containers are recreated, so use names, not IPs.

## Cleanup

```bash
docker rm -f flask-api redis mysql
docker network rm my-bridge-net
docker rmi flask-api:1.0
```
