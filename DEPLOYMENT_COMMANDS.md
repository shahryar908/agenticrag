# Quick Deployment Commands

## 🚀 **One-Time Setup**

```bash
# 1. Create EKS Cluster
eksctl create cluster --name rag-production --region us-east-1 --nodes 2

# 2. Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name rag-production

# 3. Verify cluster
kubectl get nodes
```

## 📦 **Manual Deployment (Without CI/CD)**

```bash
# Build Docker image
docker build -t shahryar371/rag-system-image:latest .

# Push to DockerHub
docker push shahryar371/rag-system-image:latest

# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n rag-system
kubectl get svc -n rag-system
```

## 🔄 **With CI/CD (Automatic)**

```bash
# Just push code!
git add .
git commit -m "Update RAG system"
git push origin main

# CI/CD does everything automatically
# Watch at: https://github.com/YOUR_USERNAME/RAG/actions
```

## 📊 **Monitoring Commands**

```bash
# View pods
kubectl get pods -n rag-system

# View logs
kubectl logs -f deployment/rag-system-deployment -n rag-system

# View service
kubectl get svc -n rag-system

# Describe deployment
kubectl describe deployment rag-system-deployment -n rag-system

# Port forward (for local testing)
kubectl port-forward svc/rag-system-service 8000:80 -n rag-system
```

## 🔧 **Useful Commands**

```bash
# Scale deployment
kubectl scale deployment rag-system-deployment --replicas=3 -n rag-system

# Restart deployment
kubectl rollout restart deployment/rag-system-deployment -n rag-system

# Rollback deployment
kubectl rollout undo deployment/rag-system-deployment -n rag-system

# Delete everything
kubectl delete namespace rag-system

# Delete cluster
eksctl delete cluster --name rag-production --region us-east-1
```

## 🐛 **Debugging**

```bash
# Get pod name
kubectl get pods -n rag-system

# Exec into pod
kubectl exec -it POD_NAME -n rag-system -- /bin/bash

# View pod logs
kubectl logs POD_NAME -n rag-system

# Describe pod (see errors)
kubectl describe pod POD_NAME -n rag-system

# Check events
kubectl get events -n rag-system --sort-by='.lastTimestamp'
```

## 🔐 **Secrets Management**

```bash
# Create secret
kubectl create secret generic rag-system-secret \
  --from-literal=GROQ_API_KEY=your_key_here \
  -n rag-system

# View secrets
kubectl get secrets -n rag-system

# Describe secret
kubectl describe secret rag-system-secret -n rag-system

# Delete secret
kubectl delete secret rag-system-secret -n rag-system
```

## 📈 **Auto-Scaling**

```bash
# Enable HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment rag-system-deployment \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n rag-system

# Check HPA status
kubectl get hpa -n rag-system
```