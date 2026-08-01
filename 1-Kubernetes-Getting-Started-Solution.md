# Solution: Exercise 1 - Kubernetes Getting Started

Goal: deploy a web app (nginx) on Kubernetes so it is always running, portable, and can be scaled later.

Environment: Windows 11, Docker Desktop, Minikube v1.39.0 (docker driver), kubectl via Docker Desktop.

## Prerequisite: install Minikube

```powershell
winget install --id Kubernetes.minikube -e
```

Docker Desktop must be running.

## Steps and actual output

### 1. Start a local cluster

```bash
minikube start --driver=docker
```

```
* Using the docker driver based on user configuration
* Preparing Kubernetes v1.37.0 on containerd 2.3.4 ...
* Enabled addons: storage-provisioner, default-storageclass
* Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

Wait for the node to be Ready before creating anything:

```bash
kubectl wait --for=condition=Ready node/minikube --timeout=180s
```

### 2. Create a Pod running nginx

```bash
kubectl run hello-k8s --image=nginx --port=80
```

```
pod/hello-k8s created
```

### 3. Verify the Pod

```bash
kubectl get pods
```

```
NAME        READY   STATUS    RESTARTS   AGE
hello-k8s   1/1     Running   0          18s
```

### 4. Expose the Pod as a Service

```bash
kubectl expose pod hello-k8s --type=NodePort --port=80
kubectl get svc hello-k8s
```

```
service/hello-k8s exposed

NAME        TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
hello-k8s   NodePort   10.101.37.213   <none>        80:30331/TCP   0s
```

### 5. Open the app in a browser

```bash
minikube service hello-k8s
```

With the docker driver on Windows this opens a tunnel and keeps running; leave the terminal open (Ctrl+C to stop).
It prints a `http://127.0.0.1:<port>` URL and opens it in the browser.

Alternative check using port-forward:

```bash
kubectl port-forward svc/hello-k8s 8080:80
curl http://localhost:8080
```

Verified result: `HTTP 200` and `<title>Welcome to nginx!</title>`.

## Notes

- First attempt: `kubectl run` failed with `serviceaccount "default" not found` because it ran seconds after
  `minikube start`, before the node was Ready. Waiting for the node (see step 1) fixes it.
- A bare Pod is not restarted if it is deleted and cannot be scaled. For "always running and scalable",
  the next step is a Deployment:
  `kubectl create deployment hello-k8s --image=nginx --replicas=3`.

## Cleanup

```bash
kubectl delete svc hello-k8s
kubectl delete pod hello-k8s
minikube stop
```
