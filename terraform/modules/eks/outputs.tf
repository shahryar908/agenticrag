output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "Kubernetes version of the cluster"
  value       = aws_eks_cluster.main.version
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "Security group ID of the cluster"
  value       = aws_security_group.cluster.id
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN of the cluster"
  value       = aws_iam_role.cluster.arn
}

output "node_group_id" {
  description = "Node group ID"
  value       = aws_eks_node_group.main.id
}

output "node_group_status" {
  description = "Status of the node group"
  value       = aws_eks_node_group.main.status
}

output "node_iam_role_arn" {
  description = "IAM role ARN of the nodes"
  value       = aws_iam_role.node.arn
}

output "oidc_provider_arn" {
  description = "ARN of the OIDC provider"
  value       = aws_iam_openid_connect_provider.cluster.arn
}
