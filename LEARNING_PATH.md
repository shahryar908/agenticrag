# DevOps Learning Path - From Basics to Production

This guide explains every DevOps concept in your project, step by step.

---

## Table of Contents

1. [Part 1: Basic Concepts](#part-1-basic-concepts)
2. [Part 2: Docker & Containers](#part-2-docker--containers)
3. [Part 3: Kubernetes Basics](#part-3-kubernetes-basics)
4. [Part 4: Infrastructure as Code (Terraform)](#part-4-infrastructure-as-code-terraform)
5. [Part 5: CI/CD Pipeline](#part-5-cicd-pipeline)
6. [Part 6: Monitoring & Logging](#part-6-monitoring--logging)
7. [Part 7: Putting It All Together](#part-7-putting-it-all-together)

---

## Part 1: Basic Concepts

### What is DevOps?

**DevOps = Development + Operations**

**Before DevOps:**
- Developers write code
- Operations team deploys it manually
- Takes days/weeks to deploy
- Many errors and downtime

**With DevOps:**
- Everything is automated
- Developers can deploy anytime
- Takes minutes to deploy
- Fewer errors, more reliability

### Key Principles

1. **Automation**: No manual work
2. **Version Control**: Track all changes
3. **Continuous Integration**: Merge code frequently
4. **Continuous Deployment**: Deploy automatically
5. **Monitoring**: Know what's happening
6. **Infrastructure as Code**: Infrastructure in Git

### Your Project's DevOps Flow

```
Code Change → Git Push → GitHub Actions → Build Docker → Deploy to K8s → Monitor
```

**Time**: ~10 minutes from code to production

---

## Part 2: Docker & Containers

### What is Docker?

**Problem**: "It works on my machine" but not on server

**Solution**: Package everything (code + dependencies + OS) into a container

### Basic Concepts

**Image**: Blueprint (like a recipe)
**Container**: Running instance (like a cooked meal)

### Your Dockerfile Explained

```dockerfile
# Start with Python 3.11 base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv package manager
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Health check (is app running?)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the app
CMD ["uv", "run", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### What Each Part Does

1. **FROM**: Base operating system + Python
2. **WORKDIR**: Where to put files inside container
3. **COPY**: Copy files from your computer to container
4. **RUN**: Execute commands during build
5. **EXPOSE**: Tell Docker which port to use
6. **HEALTHCHECK**: Check if app is healthy
7. **CMD**: Command to run when container starts

### Try It Yourself

```bash
# Build Docker image
docker build -t my-rag-app .

# Run container
docker run -p 8000:8000 my-rag-app

# Check running containers
docker ps

# View logs
docker logs <container-id>

# Stop container
docker stop <container-id>
```

### Docker Commands Cheat Sheet

```bash
docker build -t name .          # Build image
docker images                   # List images
docker run -p 8000:8000 name   # Run container
docker ps                       # List running containers
docker ps -a                    # List all containers
docker logs <id>                # View logs
docker exec -it <id> bash      # Enter container
docker stop <id>                # Stop container
docker rm <id>                  # Remove container
docker rmi <image>              # Remove image
```

---

## Part 3: Kubernetes Basics

### What is Kubernetes (K8s)?

**Problem**: Managing 100s of Docker containers manually

**Solution**: Kubernetes orchestrates (manages) containers automatically

### Why Kubernetes?

Without K8s:
- Container crashes → App is down
- Need to scale → Manually start more containers
- Update app → Downtime

With K8s:
- Container crashes → K8s restarts it automatically
- Need to scale → K8s adds more containers
- Update app → K8s does rolling update (no downtime)

### Core Concepts

#### 1. Pod
- Smallest unit in K8s
- Contains 1+ containers
- Has its own IP address

```
Pod = Running container(s) on K8s
```

#### 2. Deployment
- Manages Pods
- Ensures desired number of Pods are running
- Handles updates and rollbacks

```yaml
# k8s/deployment.yml
replicas: 2  # Run 2 copies of the app
```

If 1 Pod crashes, K8s automatically starts a new one!

#### 3. Service
- Exposes Pods to network
- Load balances traffic across Pods
- Gives stable IP/DNS name

```
Users → Service → Pod 1
                → Pod 2
```

#### 4. Namespace
- Virtual cluster within cluster
- Isolates resources

```
rag-system namespace:
  - Your app Pods
  - Your app Service
  - Your app Secrets

monitoring namespace:
  - Prometheus
  - Grafana
```

#### 5. ConfigMap
- Store configuration (non-sensitive)

```yaml
ConfigMap:
  APP_ENV: production
  LOG_LEVEL: info
```

#### 6. Secret
- Store sensitive data (passwords, API keys)

```yaml
Secret:
  GROQ_API_KEY: your-key (base64 encoded)
```

### Your Kubernetes Files Explained

#### namespace.yml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: rag-system
```

Creates isolated space called "rag-system"

#### deployment.yml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-system-deployment
  namespace: rag-system
spec:
  replicas: 2  # Run 2 Pods
  selector:
    matchLabels:
      app: rag-system
  template:
    metadata:
      labels:
        app: rag-system
    spec:
      containers:
      - name: rag-api
        image: shahryar371/rag-system-image:latest
        ports:
        - containerPort: 8000
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-system-secret
              key: GROQ_API_KEY
```

**What this does:**
1. Create 2 replicas (copies) of your app
2. Use Docker image from DockerHub
3. Expose port 8000
4. Inject GROQ_API_KEY from Secret

#### service.yml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-system-service
  namespace: rag-system
spec:
  type: LoadBalancer  # External access
  selector:
    app: rag-system
  ports:
  - port: 80          # External port
    targetPort: 8000  # Container port
```

**What this does:**
1. Create AWS Load Balancer
2. Route traffic from port 80 to your Pods on port 8000
3. Balance load across 2 Pods

### Kubernetes Commands Cheat Sheet

```bash
# View resources
kubectl get pods                    # List Pods
kubectl get deployments             # List Deployments
kubectl get services                # List Services
kubectl get all                     # List everything

# Describe (detailed info)
kubectl describe pod <pod-name>
kubectl describe deployment <name>

# Logs
kubectl logs <pod-name>             # View logs
kubectl logs -f <pod-name>          # Follow logs

# Execute commands in Pod
kubectl exec -it <pod-name> -- bash

# Apply changes
kubectl apply -f k8s/               # Deploy all files
kubectl apply -f deployment.yml     # Deploy single file

# Scale
kubectl scale deployment rag-system-deployment --replicas=5

# Delete
kubectl delete pod <pod-name>
kubectl delete -f deployment.yml

# Namespace-specific
kubectl get pods -n rag-system
kubectl logs <pod-name> -n rag-system
```

### Hands-On Exercise

```bash
# 1. View your Pods
kubectl get pods -n rag-system

# 2. Check Pod details
kubectl describe pod <pod-name> -n rag-system

# 3. View logs
kubectl logs -f <pod-name> -n rag-system

# 4. Scale to 3 replicas
kubectl scale deployment rag-system-deployment --replicas=3 -n rag-system

# 5. Watch Pods being created
kubectl get pods -n rag-system -w

# 6. Delete a Pod (K8s will recreate it!)
kubectl delete pod <pod-name> -n rag-system

# 7. Watch new Pod being created
kubectl get pods -n rag-system -w
```

---

## Part 4: Infrastructure as Code (Terraform)

### What is Infrastructure as Code?

**Problem**: Creating AWS resources manually
- Click through AWS Console
- Takes hours
- Hard to replicate
- No version control

**Solution**: Write infrastructure in code

```hcl
# terraform/main.tf
resource "aws_eks_cluster" "main" {
  name = "rag-production"
}
```

Run `terraform apply` → Infrastructure created!

### Why Terraform?

1. **Reproducible**: Create identical environments
2. **Version Controlled**: Track changes in Git
3. **Automated**: No manual clicking
4. **Multi-Cloud**: Works with AWS, Azure, GCP

### Terraform Basics

#### 1. Providers
Tell Terraform which cloud to use

```hcl
provider "aws" {
  region = "us-east-1"
}
```

#### 2. Resources
Things to create (EC2, VPC, EKS, etc.)

```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
```

#### 3. Variables
Input values

```hcl
variable "cluster_name" {
  default = "rag-production"
}
```

#### 4. Outputs
Return values

```hcl
output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}
```

#### 5. Modules
Reusable components

```
modules/
  vpc/        # VPC creation
  eks/        # EKS cluster
  monitoring/ # Prometheus/Grafana
```

### Your Terraform Structure Explained

```
terraform/
├── main.tf              # Main configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars     # Your values (NOT in Git)
│
└── modules/
    ├── vpc/            # Network (subnets, NAT, etc.)
    ├── eks/            # Kubernetes cluster
    └── monitoring/     # Prometheus & Grafana
```

### What Terraform Creates

When you run `terraform apply`:

1. **VPC Module**
   - Virtual Private Cloud
   - 3 public subnets (for Load Balancers)
   - 3 private subnets (for EKS nodes)
   - Internet Gateway
   - NAT Gateways
   - Route Tables

2. **EKS Module**
   - EKS Cluster (Kubernetes control plane)
   - Node Group (EC2 instances)
   - IAM Roles (permissions)
   - Security Groups (firewall)

3. **Monitoring Module**
   - Prometheus (metrics)
   - Grafana (dashboards)

### Terraform Workflow

```bash
# 1. Initialize (download providers)
terraform init

# 2. Plan (preview changes)
terraform plan

# 3. Apply (create infrastructure)
terraform apply

# 4. Show resources
terraform show

# 5. Destroy (delete everything)
terraform destroy
```

### Terraform State

Terraform tracks what it created in a **state file**:

```
terraform.tfstate  # Current infrastructure
```

**IMPORTANT**:
- Contains sensitive data
- Never commit to Git
- In production, store in S3

### Hands-On Exercise

```bash
cd terraform

# 1. Initialize
terraform init

# 2. Validate syntax
terraform validate

# 3. Preview changes
terraform plan

# 4. See what will be created
# Read the output carefully!

# 5. Create infrastructure (takes 15-20 min)
# terraform apply
# Type 'yes' when prompted

# 6. View outputs
terraform output

# 7. See all resources
terraform state list

# 8. Destroy (when done testing)
# terraform destroy
```

---

## Part 5: CI/CD Pipeline

### What is CI/CD?

**CI (Continuous Integration)**:
- Merge code frequently
- Run tests automatically
- Catch bugs early

**CD (Continuous Deployment)**:
- Deploy automatically
- No manual steps
- Deploy multiple times per day

### Your Pipeline Flow

```
1. You push code to GitHub
   ↓
2. GitHub Actions triggers
   ↓
3. Build & Test Job
   - Checkout code
   - Install dependencies
   - Run tests
   ↓
4. Docker Build Job
   - Build Docker image
   - Push to DockerHub
   ↓
5. Deploy to EKS Job
   - Configure kubectl
   - Deploy to Kubernetes
   - Verify deployment
   ↓
6. App is LIVE!
```

**Total Time**: 7-10 minutes

### GitHub Actions Explained

File: `.github/workflows/deploy.yml`

#### Structure

```yaml
name: Build and Deploy to EKS

on:                    # When to run?
  push:
    branches:
      - main          # On push to main

env:                   # Environment variables
  DOCKER_IMAGE: shahryar371/rag-system-image

jobs:                  # What to do?
  build:              # Job 1
  docker:             # Job 2
  deploy:             # Job 3
```

#### Job 1: Build & Test

```yaml
build:
  runs-on: ubuntu-latest  # Use Ubuntu VM

  steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install uv
        uv sync
```

**What this does:**
1. Spin up Ubuntu VM
2. Download your code
3. Install Python 3.11
4. Install dependencies

#### Job 2: Build Docker Image

```yaml
docker:
  needs: build        # Wait for build job

  steps:
    - name: Login to DockerHub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        push: true
        tags: shahryar371/rag-system-image:latest
```

**What this does:**
1. Login to DockerHub
2. Build Docker image
3. Push to DockerHub

#### Job 3: Deploy to EKS

```yaml
deploy:
  needs: docker       # Wait for docker job

  steps:
    - name: Configure AWS
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name rag-production

    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
```

**What this does:**
1. Configure AWS credentials
2. Connect to EKS cluster
3. Deploy to Kubernetes

### GitHub Secrets

Sensitive data stored securely:

```
DOCKERHUB_USERNAME      → Your DockerHub username
DOCKERHUB_TOKEN         → DockerHub access token
AWS_ACCESS_KEY_ID       → AWS credentials
AWS_SECRET_ACCESS_KEY   → AWS credentials
GROQ_API_KEY           → Groq API key
```

**How to add:**
1. Go to repo → Settings
2. Secrets and variables → Actions
3. New repository secret
4. Add name and value

### Viewing Pipeline Runs

1. Go to: https://github.com/shahryar908/agenticrag/actions
2. Click on a workflow run
3. See each job's logs
4. Debug any failures

### Common Pipeline Issues

#### Build Fails
```
Error: Module not found
```
**Fix**: Check pyproject.toml has all dependencies

#### Docker Build Fails
```
Error: Cannot connect to Docker daemon
```
**Fix**: GitHub Actions handles this automatically

#### Deploy Fails
```
Error: EKS cluster not found
```
**Fix**: Create EKS cluster first with Terraform

#### Secrets Missing
```
Error: Secret AWS_ACCESS_KEY_ID not found
```
**Fix**: Add secret in GitHub Settings

---

## Part 6: Monitoring & Logging

### Why Monitor?

**Without Monitoring:**
- App crashes → You don't know
- Slow response → Users complain
- High memory → Server crashes

**With Monitoring:**
- Know everything in real-time
- Get alerts before users notice
- Debug issues quickly

### Prometheus (Metrics)

**What it does**: Collects numbers (metrics)

Examples:
- CPU usage: 45%
- Memory usage: 2GB
- HTTP requests: 1000/min
- Response time: 350ms

**How it works:**
1. Prometheus scrapes metrics from Pods
2. Stores time-series data
3. Alerts when thresholds exceeded

### Grafana (Visualization)

**What it does**: Shows metrics in dashboards

Examples:
- Line charts: Response time over time
- Gauges: Current CPU usage
- Tables: Error logs

**Your Grafana Dashboard:**
```
http://localhost:3000
Username: admin
Password: admin
```

### Key Metrics to Monitor

1. **Infrastructure**
   - CPU usage
   - Memory usage
   - Disk space
   - Network traffic

2. **Application**
   - Request rate
   - Response time
   - Error rate
   - Success rate

3. **Business**
   - Active users
   - Documents uploaded
   - Questions asked

### Accessing Monitoring

```bash
# Port-forward Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Open: http://localhost:9090

# Port-forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80

# Open: http://localhost:3000
```

---

## Part 7: Putting It All Together

### Complete Flow: Code to Production

```
Day 1: Setup Infrastructure
├─ Run Terraform
│  ├─ Creates VPC
│  ├─ Creates EKS cluster
│  ├─ Creates node groups
│  └─ Deploys monitoring
└─ Takes 15-20 minutes

Day 2+: Daily Development
├─ Make code changes
├─ Git commit & push
│  ↓
├─ CI/CD Pipeline (automatic)
│  ├─ Build & test
│  ├─ Build Docker image
│  ├─ Push to DockerHub
│  └─ Deploy to EKS
└─ Live in 10 minutes!
```

### Architecture Diagram Explained

```
┌─────────────────────────────────────────┐
│          USERS (Internet)               │
└────────────────┬────────────────────────┘
                 ↓
       [AWS Load Balancer]  ← Created by Service
                 ↓
    ┌────────────────────────┐
    │  Kubernetes (EKS)      │ ← Created by Terraform
    │                        │
    │  ┌──────────────────┐ │
    │  │ Pod 1 (RAG API)  │ │ ← Created by Deployment
    │  └──────────────────┘ │
    │  ┌──────────────────┐ │
    │  │ Pod 2 (RAG API)  │ │ ← Replica for HA
    │  └──────────────────┘ │
    │                        │
    │  ┌──────────────────┐ │
    │  │  Prometheus      │ │ ← Monitoring
    │  └──────────────────┘ │
    │  ┌──────────────────┐ │
    │  │  Grafana         │ │ ← Dashboards
    │  └──────────────────┘ │
    └────────────────────────┘
             ↑
    [Managed by Terraform]
    [Deployed by GitHub Actions]
```

### What Happens When...

#### User Makes a Request
```
1. User → http://load-balancer-url/ask
2. Load Balancer → Routes to Pod 1 or Pod 2
3. Pod processes request
4. Returns response
5. Prometheus records metrics
```

#### You Push Code
```
1. git push origin main
2. GitHub Actions triggers
3. Builds new Docker image
4. Pushes to DockerHub
5. Updates Kubernetes
6. K8s does rolling update:
   - Starts new Pod with new code
   - Waits for health check
   - Stops old Pod
   - No downtime!
```

#### Pod Crashes
```
1. Pod crashes
2. K8s detects (health check fails)
3. K8s starts new Pod
4. Takes ~30 seconds
5. Service routes traffic to healthy Pods
6. No user impact!
```

### Production Checklist

- [ ] Terraform creates infrastructure
- [ ] EKS cluster running
- [ ] GitHub Secrets configured
- [ ] CI/CD pipeline working
- [ ] App deployed to K8s
- [ ] Load Balancer has public URL
- [ ] Monitoring accessible
- [ ] Logs viewable

### Interview Questions & Answers

**Q: Walk me through your deployment process**

A: "I use a fully automated CI/CD pipeline. When I push code to GitHub, GitHub Actions triggers three jobs: build & test, Docker image creation, and deployment to EKS. The entire process takes about 10 minutes, and Kubernetes does a rolling update with zero downtime."

**Q: How do you handle infrastructure?**

A: "I use Terraform for Infrastructure as Code. All my AWS resources - VPC, EKS cluster, security groups, and IAM roles - are defined in Terraform modules. This makes the infrastructure reproducible and version-controlled."

**Q: What if a container crashes?**

A: "Kubernetes automatically restarts crashed containers. I have 2 replicas running, so if one crashes, the other handles traffic while K8s spins up a replacement. I also have health checks and readiness probes configured."

**Q: How do you monitor your application?**

A: "I use Prometheus for metrics collection and Grafana for visualization. I monitor CPU, memory, request rates, and response times. I've set up alerts for critical thresholds like high error rates or slow responses."

**Q: How do you manage secrets?**

A: "Secrets are stored in Kubernetes Secrets (base64 encoded) and never committed to Git. For CI/CD, I use GitHub Secrets. In a production environment, I'd use AWS Secrets Manager or HashiCorp Vault for additional security."

### Next Learning Steps

1. **Week 1-2**: Master Docker and Kubernetes basics
2. **Week 3-4**: Learn Terraform deeply
3. **Week 5**: Advanced CI/CD patterns
4. **Week 6**: Monitoring and alerting
5. **Week 7**: Security best practices
6. **Week 8**: Cost optimization

### Resources

- **Docker**: https://docs.docker.com/get-started/
- **Kubernetes**: https://kubernetes.io/docs/tutorials/
- **Terraform**: https://learn.hashicorp.com/terraform
- **AWS EKS**: https://docs.aws.amazon.com/eks/
- **GitHub Actions**: https://docs.github.com/en/actions

---

**You now understand every piece of your DevOps infrastructure!**

Start with Part 2 (Docker) and work your way through each section hands-on.