# =========================================
# Terraform Variables
# =========================================
# Define all input variables here
# Override values in terraform.tfvars
# =========================================

# =========================================
# General Variables
# =========================================

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "production"
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "shahryar371"
}

# =========================================
# EKS Cluster Variables
# =========================================

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "rag-production"
}

variable "cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

# =========================================
# VPC Variables
# =========================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# =========================================
# Node Group Variables
# =========================================

variable "node_instance_types" {
  description = "Instance types for EKS node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 4
}

variable "node_disk_size" {
  description = "Disk size in GB for each node"
  type        = number
  default     = 20
}

# =========================================
# Application Variables
# =========================================

variable "groq_api_key" {
  description = "Groq API key for RAG system"
  type        = string
  sensitive   = true
  default     = ""
}

# =========================================
# Monitoring Variables
# =========================================

variable "enable_prometheus" {
  description = "Enable Prometheus monitoring"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana dashboards"
  type        = bool
  default     = true
}

# =========================================
# Cost Optimization Variables
# =========================================

variable "enable_spot_instances" {
  description = "Use Spot instances for cost savings (70% cheaper)"
  type        = bool
  default     = false
}

variable "spot_instance_types" {
  description = "Instance types for spot instances"
  type        = list(string)
  default     = ["t3.medium", "t3a.medium"]
}

# =========================================
# Tags
# =========================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}