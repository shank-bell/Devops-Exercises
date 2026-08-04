import os
import time

import pymysql
import redis
from flask import Flask, jsonify

app = Flask(__name__)

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "rootpass")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

cache = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


def db_connection():
    return pymysql.connect(host=MYSQL_HOST, user="root", password=MYSQL_PASSWORD, autocommit=True)


@app.get("/")
def index():
    return jsonify(message="Flask API on a custom Docker bridge network", endpoints=["/health", "/visit", "/db"])


@app.get("/health")
def health():
    status = {}
    try:
        status["redis"] = "up" if cache.ping() else "down"
    except Exception as exc:
        status["redis"] = f"down: {exc}"
    try:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        status["mysql"] = "up"
    except Exception as exc:
        status["mysql"] = f"down: {exc}"
    return jsonify(status)


@app.get("/visit")
def visit():
    # Redis container, reached by its container name
    return jsonify(visits=cache.incr("visits"), source=f"redis@{REDIS_HOST}")


@app.get("/db")
def db():
    # MySQL container, reached by its container name
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute("CREATE DATABASE IF NOT EXISTS labdb")
        cur.execute("CREATE TABLE IF NOT EXISTS labdb.hits (id INT AUTO_INCREMENT PRIMARY KEY, ts DOUBLE)")
        cur.execute("INSERT INTO labdb.hits (ts) VALUES (%s)", (time.time(),))
        cur.execute("SELECT COUNT(*) FROM labdb.hits")
        (count,) = cur.fetchone()
    return jsonify(rows_in_mysql=count, source=f"mysql@{MYSQL_HOST}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
