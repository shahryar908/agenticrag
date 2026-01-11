variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for monitoring"
  type        = string
  default     = "monitoring"
}

variable "enable_prometheus" {
  description = "Enable Prometheus"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana"
  type        = bool
  default     = true
}
