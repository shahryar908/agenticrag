output "monitoring_namespace" {
  description = "Monitoring namespace"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "prometheus_service" {
  description = "Prometheus service name"
  value       = var.enable_prometheus ? kubernetes_service.prometheus[0].metadata[0].name : ""
}

output "grafana_service" {
  description = "Grafana service name"
  value       = var.enable_grafana ? kubernetes_service.grafana[0].metadata[0].name : ""
}

output "grafana_url" {
  description = "Grafana URL (after LoadBalancer is provisioned)"
  value       = var.enable_grafana ? "kubectl port-forward -n monitoring svc/grafana 3000:80" : ""
}
