# =========================================
# Monitoring Module
# =========================================
# Creates:
# - Prometheus for metrics
# - Grafana for visualization
# - Kubernetes resources
# =========================================

# =========================================
# Monitoring Namespace
# =========================================

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.namespace
    labels = {
      name = var.namespace
    }
  }
}

# =========================================
# Prometheus ConfigMap
# =========================================

resource "kubernetes_config_map" "prometheus" {
  count = var.enable_prometheus ? 1 : 0

  metadata {
    name      = "prometheus-config"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
  }

  data = {
    "prometheus.yml" = <<-EOT
      global:
        scrape_interval: 15s
        evaluation_interval: 15s

      scrape_configs:
        - job_name: 'kubernetes-nodes'
          kubernetes_sd_configs:
            - role: node
          relabel_configs:
            - action: labelmap
              regex: __meta_kubernetes_node_label_(.+)

        - job_name: 'kubernetes-pods'
          kubernetes_sd_configs:
            - role: pod
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
              action: keep
              regex: true
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
              action: replace
              target_label: __metrics_path__
              regex: (.+)
            - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
              action: replace
              regex: ([^:]+)(?::\d+)?;(\d+)
              replacement: $1:$2
              target_label: __address__
    EOT
  }
}

# =========================================
# Prometheus Deployment
# =========================================

resource "kubernetes_deployment" "prometheus" {
  count = var.enable_prometheus ? 1 : 0

  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "prometheus"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "prometheus"
      }
    }

    template {
      metadata {
        labels = {
          app = "prometheus"
        }
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9090"
        }
      }

      spec {
        container {
          name  = "prometheus"
          image = "prom/prometheus:latest"

          port {
            container_port = 9090
          }

          volume_mount {
            name       = "config"
            mount_path = "/etc/prometheus"
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.prometheus[0].metadata[0].name
          }
        }
      }
    }
  }
}

# =========================================
# Prometheus Service
# =========================================

resource "kubernetes_service" "prometheus" {
  count = var.enable_prometheus ? 1 : 0

  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "prometheus"
    }
  }

  spec {
    selector = {
      app = "prometheus"
    }

    port {
      port        = 9090
      target_port = 9090
    }

    type = "ClusterIP"
  }
}

# =========================================
# Grafana Deployment
# =========================================

resource "kubernetes_deployment" "grafana" {
  count = var.enable_grafana ? 1 : 0

  metadata {
    name      = "grafana"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "grafana"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "grafana"
      }
    }

    template {
      metadata {
        labels = {
          app = "grafana"
        }
      }

      spec {
        container {
          name  = "grafana"
          image = "grafana/grafana:latest"

          port {
            container_port = 3000
          }

          env {
            name  = "GF_SECURITY_ADMIN_PASSWORD"
            value = "admin"
          }

          env {
            name  = "GF_USERS_ALLOW_SIGN_UP"
            value = "false"
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }
        }
      }
    }
  }
}

# =========================================
# Grafana Service
# =========================================

resource "kubernetes_service" "grafana" {
  count = var.enable_grafana ? 1 : 0

  metadata {
    name      = "grafana"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "grafana"
    }
  }

  spec {
    selector = {
      app = "grafana"
    }

    port {
      port        = 80
      target_port = 3000
    }

    type = "LoadBalancer"
  }
}
