# =========================================
# Main Terraform Configuration
# =========================================
# This creates:
# - VPC with public/private subnets
# - EKS cluster
# - Node groups
# - Security groups
# - IAM roles
# =========================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }

  # Optional: Store state in S3 (recommended for production)
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "rag-system/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

# =========================================
# Provider Configuration
# =========================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "RAG-System"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}

# =========================================
# Data Sources
# =========================================

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# =========================================
# VPC Module
# =========================================

module "vpc" {
  source = "./modules/vpc"

  cluster_name = var.cluster_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  azs          = slice(data.aws_availability_zones.available.names, 0, 3)
}

# =========================================
# EKS Module
# =========================================

module "eks" {
  source = "./modules/eks"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  environment     = var.environment

  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets

  node_instance_types = var.node_instance_types
  node_desired_size   = var.node_desired_size
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size
  node_disk_size      = var.node_disk_size
}

# =========================================
# Kubernetes Provider Configuration
# =========================================

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      module.eks.cluster_name
    ]
  }
}

# =========================================
# Kubernetes Namespace for RAG System
# =========================================

resource "kubernetes_namespace" "rag_system" {
  metadata {
    name = "rag-system"
    labels = {
      name        = "rag-system"
      environment = var.environment
    }
  }

  depends_on = [module.eks]
}

# =========================================
# Kubernetes Secret for Groq API Key
# =========================================

resource "kubernetes_secret" "groq_api_key" {
  metadata {
    name      = "rag-system-secret"
    namespace = kubernetes_namespace.rag_system.metadata[0].name
  }

  data = {
    GROQ_API_KEY = var.groq_api_key
  }

  type = "Opaque"
}

# =========================================
# EBS CSI Driver Add-on (for persistent volumes)
# =========================================

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name = module.eks.cluster_name
  addon_name   = "aws-ebs-csi-driver"

  depends_on = [module.eks]
}

# =========================================
# Monitoring Module (Prometheus/Grafana)
# =========================================

module "monitoring" {
  source = "./modules/monitoring"

  cluster_name = var.cluster_name
  namespace    = "monitoring"

  enable_prometheus = var.enable_prometheus
  enable_grafana    = var.enable_grafana

  depends_on = [module.eks]
}