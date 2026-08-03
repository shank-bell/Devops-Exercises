# Solution: Exercise 3 - Scaling a Flask App with ReplicaSets

Goal: run a flash-sale Flask app on a single-node Minikube cluster, scale it with a ReplicaSet, and observe self-healing and load distribution.

Environment: Windows 11, Docker Desktop, Minikube v1.39.0 (docker driver, containerd runtime), Kubernetes v1.37.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Flask app with `/`, `/buy` and `/health`; every response includes the serving pod name |
| `Dockerfile` | Builds `flashsale:1.0` (gunicorn on port 5000) |
| `flashsale-replicaset.yaml` | ReplicaSet `flashsale-rs` (3 replicas, probes, resource limits) and ClusterIP Service `flashsale-svc` |

Notes on the exercise text:

- The Dockerfile copies the app as `app.py` because gunicorn starts `app:app`.
- The later steps in the text say `flask-app-rs`; the ReplicaSet is named `flashsale-rs`, so that name is used throughout.
- The image is built locally and loaded into Minikube instead of being pushed to Docker Hub. `imagePullPolicy: Never` makes the pods use that local image.

## Steps and actual output

### 1-2. Clean up and start a single-node cluster

```bash
minikube delete
minikube start --nodes=1 --driver=docker
kubectl get nodes
```

```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   31s   v1.37.0
```

### 3. Build the image

This cluster uses containerd, so `minikube docker-env` does not apply. Build with the local Docker and load the image:

```bash
docker build -t flashsale:1.0 .
minikube image load flashsale:1.0
```

### 4. Apply the ReplicaSet and Service

```bash
kubectl apply -f flashsale-replicaset.yaml
```

```
replicaset.apps/flashsale-rs created
service/flashsale-svc created
```

### 5. Verify pods and ReplicaSet

```bash
kubectl get pods
kubectl get rs
```

```
NAME                 READY   STATUS    RESTARTS   AGE
flashsale-rs-pf92r   1/1     Running   0          7s
flashsale-rs-wbfxb   1/1     Running   0          7s
flashsale-rs-x9sl5   1/1     Running   0          7s

NAME           DESIRED   CURRENT   READY   AGE
flashsale-rs   3         3         3       7s
```

### 6. Scale to 5 replicas

```bash
kubectl scale rs flashsale-rs --replicas=5
kubectl get rs
kubectl get pods
```

```
replicaset.apps/flashsale-rs scaled

NAME           DESIRED   CURRENT   READY   AGE
flashsale-rs   5         5         5       14s

NAME                 READY   STATUS    RESTARTS   AGE
flashsale-rs-6wpc2   1/1     Running   0          7s
flashsale-rs-77k27   1/1     Running   0          7s
flashsale-rs-pf92r   1/1     Running   0          14s
flashsale-rs-wbfxb   1/1     Running   0          14s
flashsale-rs-x9sl5   1/1     Running   0          14s
```

### 7. Delete one pod and watch it come back

```bash
kubectl delete pod flashsale-rs-6wpc2
kubectl get pods
```

```
pod "flashsale-rs-6wpc2" deleted

NAME                 READY   STATUS    RESTARTS   AGE
flashsale-rs-77k27   1/1     Running   0          14s
flashsale-rs-f7t2c   1/1     Running   0          7s      <- replacement
flashsale-rs-pf92r   1/1     Running   0          21s
flashsale-rs-wbfxb   1/1     Running   0          21s
flashsale-rs-x9sl5   1/1     Running   0          21s
```

### 8. Pod distribution across nodes

```bash
kubectl get pods -o wide
```

```
NAME                 READY   STATUS    RESTARTS   AGE   IP           NODE
flashsale-rs-77k27   1/1     Running   0          14s   10.244.0.6   minikube
flashsale-rs-f7t2c   1/1     Running   0          7s    10.244.0.8   minikube
flashsale-rs-pf92r   1/1     Running   0          21s   10.244.0.4   minikube
flashsale-rs-wbfxb   1/1     Running   0          21s   10.244.0.5   minikube
flashsale-rs-x9sl5   1/1     Running   0          21s   10.244.0.3   minikube
```

### 9. Check load distribution through the Service

From inside a pod, 40 requests to `flashsale-svc/buy`:

```bash
kubectl exec <pod> -- python -c "import urllib.request,json,collections as c; print(dict(c.Counter(json.load(urllib.request.urlopen('http://flashsale-svc/buy'))['served_by_pod'] for _ in range(40))))"
```

```
{'flashsale-rs-pf92r': 7, 'flashsale-rs-x9sl5': 8, 'flashsale-rs-wbfxb': 9, 'flashsale-rs-f7t2c': 8, 'flashsale-rs-77k27': 8}
```

Requests are spread across all five pods.

## Q&A

1. **Initial number of replicas?** 3.
2. **Pods running after applying the ReplicaSet?** 3.
3. **What happens when scaled to 5?** The ReplicaSet creates 2 more pods; 5 are running.
4. **What happens when a pod is deleted?** The ReplicaSet immediately creates a replacement, keeping the count at 5.
5. **How does Kubernetes maintain the replica count?** The ReplicaSet controller continuously compares the number of running pods with the desired count and creates or deletes pods to match.
6. **How many nodes are running?** 1.
7. **Where do the pods run?** All 5 pods run on the single node `minikube`.

## Cleanup

```bash
kubectl delete -f flashsale-replicaset.yaml
minikube stop
```
