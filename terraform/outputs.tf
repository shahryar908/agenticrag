# =========================================
# Terraform Outputs
# =========================================
# These values are shown after 'terraform apply'
# and can be used by other tools
# =========================================

# =========================================
# VPC Outputs
# =========================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of VPC"
  value       = module.vpc.vpc_cidr
}

output "private_subnets" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

# =========================================
# EKS Cluster Outputs
# =========================================

output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS cluster API server"
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "Kubernetes version of the cluster"
  value       = module.eks.cluster_version
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN of the EKS cluster"
  value       = module.eks.cluster_iam_role_arn
}

# =========================================
# Node Group Outputs
# =========================================

output "node_group_id" {
  description = "EKS node group ID"
  value       = module.eks.node_group_id
}

output "node_group_status" {
  description = "Status of the EKS node group"
  value       = module.eks.node_group_status
}

output "node_iam_role_arn" {
  description = "IAM role ARN for EKS nodes"
  value       = module.eks.node_iam_role_arn
}

# =========================================
# kubectl Configuration
# =========================================

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# =========================================
# Application Access
# =========================================

output "rag_system_namespace" {
  description = "Kubernetes namespace for RAG system"
  value       = kubernetes_namespace.rag_system.metadata[0].name
}

# =========================================
# Monitoring Outputs
# =========================================

output "prometheus_enabled" {
  description = "Whether Prometheus is enabled"
  value       = var.enable_prometheus
}

output "grafana_enabled" {
  description = "Whether Grafana is enabled"
  value       = var.enable_grafana
}

# =========================================
# Cost Information
# =========================================

output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD"
  value = format(
    "EKS Control Plane: $75, Nodes (%dx %s): ~$%d, Total: ~$%d/month",
    var.node_desired_size,
    var.node_instance_types[0],
    var.node_desired_size * 35,
    75 + (var.node_desired_size * 35)
  )
}

# =========================================
# Quick Start Commands
# =========================================

output "quick_start" {
  description = "Quick start commands"
  value = <<-EOT

  [SUCCESS] Terraform deployment complete!

  Next steps:

  1. Configure kubectl:
     ${format("aws eks update-kubeconfig --region %s --name %s", var.aws_region, module.eks.cluster_name)}

  2. Verify cluster:
     kubectl get nodes

  3. Deploy RAG system:
     kubectl apply -f k8s/

  4. Check deployment:
     kubectl get pods -n rag-system
     kubectl get svc -n rag-system

  5. Access Grafana (if enabled):
     kubectl port-forward -n monitoring svc/grafana 3000:80

  Cluster Details:
  - Name: ${module.eks.cluster_name}
  - Region: ${var.aws_region}
  - Version: ${module.eks.cluster_version}
  - Nodes: ${var.node_desired_size}
  - Type: ${var.node_instance_types[0]}

  EOT
}