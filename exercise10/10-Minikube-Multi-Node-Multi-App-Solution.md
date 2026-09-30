# Solution: Exercise 10 - Multi-Node Minikube with Multiple Applications

Goal: deploy two Flask services on a 3-node Minikube cluster, spread across nodes with pod anti-affinity: Product Catalog (2 replicas) and Shopping Cart (3 replicas).

Environment: Windows 11, Docker Desktop (4 CPUs, about 7.7 GB), Minikube v1.39.0 (docker driver, containerd), Kubernetes v1.37.

## Files

| File | Purpose |
|------|---------|
| `product_catalog.py`, `shopping_cart.py` | The two Flask apps (port 80) |
| `Dockerfile.product`, `Dockerfile.shopping` | Image builds |
| `product_catalog_deployment.yaml`, `shopping_cart_deployment.yaml` | Deployments with `podAntiAffinity` |
| `product_catalog_service.yaml`, `shopping_cart_service.yaml` | NodePort Services |

## Differences from the exercise text

- The Shopping Cart Deployment in the exercise is in namespace `devops-exercise`, but its Service is in `default`. A Service only selects pods in its own namespace, so it would have no endpoints. Everything is in `default` here.
- `--force` (needed for root on Linux) is not used on Windows.
- Each node was given `--memory=1800 --cpus=2` so three nodes fit in Docker Desktop's memory. The Jenkins container was stopped (not removed) to free memory.
- Services were tested with `kubectl port-forward` instead of `minikube service`, which keeps a tunnel open with the Docker driver on Windows.
- A new profile `devops-multinode` was created; the default `minikube` profile was left stopped, not deleted.

## Steps and results

### 1. Three-node cluster and registry addon

```bash
minikube start --nodes 3 -p devops-multinode --memory=1800 --cpus=2
minikube -p devops-multinode addons enable registry
kubectl get nodes
```

```
NAME                   STATUS   ROLES           AGE    VERSION
devops-multinode       Ready    control-plane   2m3s   v1.37.0
devops-multinode-m02   Ready    <none>          71s    v1.37.0
devops-multinode-m03   Ready    <none>          25s    v1.37.0
```

### 2. Build the images and load them on every node

```bash
docker build -t product-catalog:latest -f Dockerfile.product .
docker build -t shopping-cart:latest -f Dockerfile.shopping .
minikube -p devops-multinode image load product-catalog:latest
minikube -p devops-multinode image load shopping-cart:latest
minikube -p devops-multinode ssh -n <node> -- sudo crictl images
```

Both images were present on all three nodes. This matters because the Deployments use `imagePullPolicy: Never`, so a node without the image could not start the pod. (This cluster runs containerd, so the exercise's `docker images` on the node is replaced by `crictl images`.)

### 3. Deploy

```bash
kubectl apply -f product_catalog_deployment.yaml
kubectl apply -f shopping_cart_deployment.yaml
kubectl apply -f product_catalog_service.yaml
kubectl apply -f shopping_cart_service.yaml
kubectl get pods -o wide
```

```
NAME                             READY   STATUS    NODE
product-catalog-7cb85d4f-fph7v   1/1     Running   devops-multinode-m02
product-catalog-7cb85d4f-g2lqw   1/1     Running   devops-multinode-m03
shopping-cart-6858b5f797-27ddb   1/1     Running   devops-multinode-m03
shopping-cart-6858b5f797-9br79   1/1     Running   devops-multinode
shopping-cart-6858b5f797-x4j8m   1/1     Running   devops-multinode-m02
```

Every Deployment's pods are on different nodes: that is what
`requiredDuringSchedulingIgnoredDuringExecution` with `topologyKey: kubernetes.io/hostname` enforces ("no two pods with this label on the same node"). Shopping Cart has exactly 3 replicas for 3 nodes; a 4th replica would stay Pending.

```
NAME                      TYPE       CLUSTER-IP       PORT(S)
product-catalog-service   NodePort   10.101.255.234   80:31019/TCP
shopping-cart-service     NodePort   10.104.132.107   80:32386/TCP
```

### 4. Test the services

```bash
kubectl port-forward svc/product-catalog-service 35855:80
curl http://127.0.0.1:35855/products
```

```
[{"id":1,"name":"Laptop","price":1200},{"id":2,"name":"Phone","price":800},{"id":3,"name":"Headphones","price":150}]
```

```bash
kubectl port-forward svc/shopping-cart-service 38975:80
curl http://127.0.0.1:38975/cart                       # []
curl -X POST http://127.0.0.1:38975/cart -H "Content-Type: application/json" \
     -d '{"id": 1, "name": "Laptop", "quantity": 1}'    # HTTP 201
curl http://127.0.0.1:38975/cart
```

```
[{"id":1,"name":"Laptop","quantity":1}]
```

## Observation: the cart is not shared between replicas

The cart is a Python list in each pod's memory. A port-forward stays on one pod, so the test above looks fine. Sending 12 GETs through the Service (from inside the cluster) after adding one item:

```
cart sizes: [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0]
```

Only the pod that received the POST has the item, so a client sees a different cart depending on which of the 3 pods answers. A real deployment would keep cart state in a shared store (Redis or a database) instead of process memory. The same applies to the Product Catalog if it were writable. Here it is read-only, so all replicas agree.

## Cleanup

```bash
kubectl delete -f product_catalog_service.yaml -f shopping_cart_service.yaml
kubectl delete -f product_catalog_deployment.yaml -f shopping_cart_deployment.yaml
minikube stop -p devops-multinode
minikube delete -p devops-multinode      # removes the cluster completely
```
