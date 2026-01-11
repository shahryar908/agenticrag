# Production RAG System with Full DevOps Pipeline

A production-ready Retrieval-Augmented Generation (RAG) system with complete DevOps automation, featuring agentic AI workflows, Kubernetes orchestration, and infrastructure as code.

## Features

- **Agentic RAG**: Intelligent query routing with LangGraph
- **FastAPI REST API**: High-performance API server
- **Vector Database**: ChromaDB for semantic search
- **LLM Integration**: Groq for fast inference
- **Infrastructure as Code**: Terraform for AWS EKS
- **CI/CD Pipeline**: Automated deployment with GitHub Actions
- **Monitoring**: Prometheus & Grafana
- **Container Orchestration**: Kubernetes on AWS EKS

## Quick Start

### 1. Local Development

```bash
# Install dependencies
pip install uv
uv sync

# Run the API server
uv run uvicorn api_server:app --reload

# Upload a PDF and ask questions
uv run python upload_pdf.py
```

### 2. Deploy to AWS EKS

**Option A: Using Terraform (Recommended)**

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

**Option B: Manual EKS Setup**

```bash
# Create EKS cluster
chmod +x k8s/setup-eks.sh
./k8s/setup-eks.sh

# Deploy application
kubectl apply -f k8s/
```

### 3. CI/CD Setup

See [CICD_SETUP.md](CICD_SETUP.md) for detailed instructions on setting up automated deployments.

## Architecture

```
Users → AWS Load Balancer → Kubernetes (EKS)
                              ├── RAG API Pods
                              ├── ChromaDB
                              └── Prometheus/Grafana

All managed by Terraform
```

## Documentation

- [DEVOPS_PORTFOLIO.md](DEVOPS_PORTFOLIO.md) - Complete DevOps portfolio overview
- [CICD_SETUP.md](CICD_SETUP.md) - CI/CD pipeline setup guide
- [DEPLOYMENT_COMMANDS.md](DEPLOYMENT_COMMANDS.md) - Quick deployment reference
- [terraform/README.md](terraform/README.md) - Terraform infrastructure guide

## Technology Stack

**Application:**
- Python 3.11
- FastAPI
- LangGraph
- ChromaDB
- Groq LLM

**Infrastructure:**
- AWS EKS
- Terraform
- Kubernetes
- Docker

**DevOps:**
- GitHub Actions
- Prometheus
- Grafana

## API Endpoints

- `POST /upload-pdf` - Upload PDF documents
- `POST /add-document` - Add text documents
- `POST /ask` - Ask questions about documents
- `GET /stats` - Get system statistics
- `DELETE /clear` - Clear document database

## Environment Variables

```bash
GROQ_API_KEY=your-groq-api-key
```

## Cost Estimate

Running on AWS EKS:
- EKS Control Plane: $75/month
- 2x t3.medium nodes: $70/month
- Total: ~$207/month

Can be optimized to ~$80-100/month with spot instances.

## License

MIT

## Contributing

This is a portfolio project demonstrating production DevOps practices.