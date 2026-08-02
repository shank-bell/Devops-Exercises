# Solution: Exercise 2 - Minikube, kubectl and Flask

Goal: deploy a Python Flask app (port 15000) on a local Minikube cluster using kubectl and YAML files.

Environment: Windows 11, Docker Desktop, Minikube v1.39.0 (docker driver).

## Files

| File | Purpose |
|------|---------|
| `app.py` | Flask app listening on `0.0.0.0:15000` |
| `requirements.txt` | Python dependency (`flask`) |
| `Dockerfile` | Builds the `flask-app:1.0` image |
| `flask-deployment.yaml` | Deployment, 1 replica, `imagePullPolicy: Never` |
| `flask-service.yaml` | NodePort Service `flask-app-service` (15000 -> 15000) |

## Steps

### 1. Start Minikube

```bash
minikube start --driver=docker
kubectl wait --for=condition=Ready node/minikube --timeout=180s
```

### 2. Build the image and make it available to Minikube

```bash
docker build -t flask-app:1.0 .
minikube image load flask-app:1.0
minikube image ls | grep flask
```

This cluster uses containerd, so `minikube docker-env` does not apply. The image is built with the local Docker and loaded into the cluster with `minikube image load`.

`imagePullPolicy: Never` tells Kubernetes to use this local image and never pull from a registry.

### 3. Deploy

```bash
kubectl apply -f flask-deployment.yaml
kubectl get deployments
kubectl get pods
```

```
NAME        READY   UP-TO-DATE   AVAILABLE   AGE
flask-app   1/1     1            1           0s

NAME                         READY   STATUS    RESTARTS   AGE
flask-app-54dbdf55b8-74htb   1/1     Running   0          1s
```

At this point the pod is not reachable from outside the cluster; it needs a Service.

### 4. Expose with a Service

```bash
kubectl apply -f flask-service.yaml
kubectl get svc flask-app-service
```

```
NAME                TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)           AGE
flask-app-service   NodePort   10.106.89.82   <none>        15000:32479/TCP   0s
```

Routing: external request -> Service port 15000 -> container port 15000.

### 5. Access the app

```bash
minikube service flask-app-service --url
curl <url-printed-above>
```

With the docker driver on Windows this command opens a tunnel and keeps running, so leave that terminal open and run `curl` from a second one.

Alternative check using port-forward:

```bash
kubectl port-forward svc/flask-app-service 15000:15000
curl http://localhost:15000
```

Verified result: `HTTP 200` and `Hello from Flask on Minikube!`.

## Cleanup

```bash
kubectl delete -f flask-service.yaml
kubectl delete -f flask-deployment.yaml
minikube stop
```
