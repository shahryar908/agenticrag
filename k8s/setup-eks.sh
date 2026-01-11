#!/bin/bash

# =========================================
# AWS EKS Cluster Setup Script
# =========================================

set -e

echo "Creating EKS Cluster for RAG System..."

# Variables
CLUSTER_NAME="rag-production"
REGION="us-east-1"
NODE_TYPE="t3.medium"
NODES=2
NODES_MIN=1
NODES_MAX=4

# Create EKS cluster
eksctl create cluster \
  --name $CLUSTER_NAME \
  --region $REGION \
  --nodegroup-name rag-nodes \
  --node-type $NODE_TYPE \
  --nodes $NODES \
  --nodes-min $NODES_MIN \
  --nodes-max $NODES_MAX \
  --managed

echo "Cluster created successfully!"

# Update kubeconfig
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

# Verify cluster
kubectl get nodes

echo "EKS Cluster is ready!"
echo ""
echo "Next steps:"
echo "1. kubectl apply -f k8s/"
echo "2. kubectl get svc -n rag-system"