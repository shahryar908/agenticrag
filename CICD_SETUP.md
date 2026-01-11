# CI/CD Pipeline Setup Guide

## 🎯 **What This CI/CD Does**

```
Code Change → Push to GitHub → Auto Build → Auto Test → Auto Deploy → Live in Production
```

**Every time you push code, it automatically:**
1. ✅ Builds Docker image
2. ✅ Pushes to DockerHub
3. ✅ Deploys to AWS EKS
4. ✅ Updates live application

**Time**: ~5-10 minutes from push to production

---

## 📋 **Prerequisites**

### 1. **GitHub Account** (You have this)
### 2. **DockerHub Account**
- Sign up at: https://hub.docker.com/
- Create repository: `rag-system-image`

### 3. **AWS Account**
- Sign up at: https://aws.amazon.com/
- You'll need AWS credentials

---

## 🔐 **Step 1: Set Up GitHub Secrets**

These are like passwords that GitHub Actions will use:

1. Go to your GitHub repo
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Where to Get It | Value |
|-------------|-----------------|-------|
| `DOCKERHUB_USERNAME` | DockerHub username | `shahryar371` |
| `DOCKERHUB_TOKEN` | DockerHub → Account Settings → Security → New Access Token | Your token |
| `AWS_ACCESS_KEY_ID` | AWS Console → IAM → Users → Security Credentials | Your key |
| `AWS_SECRET_ACCESS_KEY` | AWS Console → IAM → Users → Security Credentials | Your secret |
| `GROQ_API_KEY` | groq.com | `your-groq-api-key-here` |

### How to Get AWS Keys:

```bash
# Option 1: AWS Console
1. Go to AWS Console → IAM
2. Click "Users" → Your username
3. "Security credentials" tab
4. "Create access key"
5. Copy both Access Key ID and Secret

# Option 2: AWS CLI
aws iam create-access-key --user-name your-username
```

---

## 🚀 **Step 2: Create EKS Cluster**

Run this **ONE TIME** to create your Kubernetes cluster:

```bash
# Make script executable
chmod +x k8s/setup-eks.sh

# Create cluster (takes 15-20 minutes)
./k8s/setup-eks.sh
```

Or manually:

```bash
eksctl create cluster \
  --name rag-production \
  --region us-east-1 \
  --nodegroup-name rag-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed
```

**Cost**: ~$70/month for 2 t3.medium nodes

---

## 📦 **Step 3: Initial Setup**

### A. Push Code to GitHub

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial RAG system"

# Add remote (replace with your repo)
git remote add origin https://github.com/shahryar371/RAG.git

# Push to GitHub
git push -u origin main
```

### B. GitHub Actions Will Automatically:
1. Build Docker image
2. Push to DockerHub
3. Deploy to EKS

You can watch progress at:
```
https://github.com/YOUR_USERNAME/RAG/actions
```

---

## 🔄 **How CI/CD Works (Step by Step)**

### **Workflow Triggers**

```yaml
on:
  push:
    branches:
      - main  # ← Triggers on every push to main
```

### **Job 1: Build & Test** (2-3 min)
```
✓ Checkout code
✓ Install Python 3.11
✓ Install dependencies
✓ Run tests (optional)
```

### **Job 2: Docker Build** (3-4 min)
```
✓ Build Docker image
✓ Tag with 'latest' and commit SHA
✓ Push to DockerHub
```

### **Job 3: Deploy to EKS** (2-3 min)
```
✓ Configure AWS credentials
✓ Update kubeconfig
✓ Apply K8s manifests
✓ Wait for deployment
✓ Verify pods are running
```

**Total Time**: 7-10 minutes

---

## 🎬 **Daily Workflow (After Setup)**

### Making Changes:

```bash
# 1. Make code changes
vim api_server.py

# 2. Commit changes
git add .
git commit -m "Add new feature"

# 3. Push to GitHub
git push origin main

# 4. CI/CD automatically deploys!
# Watch at: https://github.com/YOUR_USERNAME/RAG/actions
```

### Check Deployment Status:

```bash
# View deployment
kubectl get pods -n rag-system

# View service URL
kubectl get svc -n rag-system

# View logs
kubectl logs -f deployment/rag-system-deployment -n rag-system
```

---

## 📊 **Understanding the Pipeline**

### **.github/workflows/deploy.yml** Breakdown:

```yaml
# When it runs
on:
  push:
    branches: [main]

# What it does
jobs:
  build:      # Step 1: Test code
  docker:     # Step 2: Build & push image
  deploy:     # Step 3: Deploy to K8s
```

### **Key Components:**

**Secrets** (stored in GitHub):
```yaml
${{ secrets.DOCKERHUB_USERNAME }}
${{ secrets.AWS_ACCESS_KEY_ID }}
${{ secrets.GROQ_API_KEY }}
```

**Environment Variables:**
```yaml
env:
  DOCKER_IMAGE: shahryar371/rag-system-image
  EKS_CLUSTER: rag-production
```

**Deployment Steps:**
```bash
1. kubectl apply -f k8s/namespace.yml
2. kubectl apply -f k8s/secrets.yml
3. kubectl apply -f k8s/deployment.yml
4. kubectl apply -f k8s/service.yml
5. kubectl rollout status
```

---

## 🔧 **Customization Options**

### **Change Cluster Name:**
Edit `.github/workflows/deploy.yml`:
```yaml
env:
  EKS_CLUSTER: my-custom-name
```

### **Change Region:**
```yaml
env:
  AWS_REGION: eu-west-1
```

### **Add Tests:**
Uncomment in workflow:
```yaml
- name: Run tests
  run: uv run pytest tests/
```

### **Change Trigger:**
```yaml
# Deploy on tag push
on:
  push:
    tags:
      - 'v*'

# Or on schedule
on:
  schedule:
    - cron: '0 0 * * *'  # Daily
```

---

## 🎯 **Production Best Practices**

### **1. Use Staging Environment**

```yaml
# Add staging deployment
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    # Deploy to staging cluster

  deploy-production:
    if: github.ref == 'refs/heads/main'
    # Deploy to production cluster
```

### **2. Add Approval Step**

```yaml
jobs:
  deploy:
    environment:
      name: production
      # Requires manual approval in GitHub
```

### **3. Rollback on Failure**

```yaml
- name: Rollback on failure
  if: failure()
  run: |
    kubectl rollout undo deployment/rag-system-deployment -n rag-system
```

---

## 💰 **Cost Breakdown**

| Service | Cost/Month | Notes |
|---------|-----------|-------|
| **AWS EKS** | $75 | Control plane |
| **EC2 (2x t3.medium)** | ~$70 | Worker nodes |
| **Load Balancer** | ~$20 | Traffic routing |
| **Storage (EBS)** | ~$10 | Database storage |
| **DockerHub** | Free | Public repos |
| **GitHub Actions** | Free | 2000 min/month free |
| **Total** | **~$175/month** | Can serve 1000s users |

**Revenue Potential**: $500-10,000/month

---

## 🐛 **Troubleshooting**

### **Build Fails:**
```bash
# Check logs in GitHub Actions
# Go to: Actions → Failed workflow → View logs
```

### **Deployment Fails:**
```bash
# Check pod status
kubectl get pods -n rag-system

# View pod logs
kubectl logs POD_NAME -n rag-system

# Describe pod for errors
kubectl describe pod POD_NAME -n rag-system
```

### **Service Not Accessible:**
```bash
# Check service
kubectl get svc -n rag-system

# Check load balancer
kubectl describe svc rag-system-service -n rag-system
```

---

## 🎓 **What You Learned**

✅ **CI/CD Concepts** - Automated deployment
✅ **GitHub Actions** - Workflow automation
✅ **Docker** - Containerization
✅ **AWS EKS** - Kubernetes on AWS
✅ **kubectl** - Kubernetes management
✅ **GitOps** - Infrastructure as code

---

## 🚀 **Next Steps**

1. **Set up monitoring** - Add Prometheus/Grafana
2. **Add logging** - ELK stack or CloudWatch
3. **Set up alerts** - PagerDuty/Slack notifications
4. **Add auto-scaling** - HPA (Horizontal Pod Autoscaler)
5. **SSL/HTTPS** - Add cert-manager for HTTPS

**Your RAG system is now production-ready with full CI/CD!** 🎉