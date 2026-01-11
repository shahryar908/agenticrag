#!/bin/bash

# =========================================
# Terraform Quick Setup Script
# =========================================

set -e

echo "========================================="
echo "RAG System - Terraform Setup"
echo "========================================="
echo ""

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "[ERROR] Terraform is not installed!"
    echo "Install from: https://www.terraform.io/downloads"
    exit 1
fi

echo "[SUCCESS] Terraform is installed: $(terraform version | head -n1)"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "[ERROR] AWS CLI is not installed!"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

echo "[SUCCESS] AWS CLI is installed: $(aws --version)"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "[ERROR] AWS credentials not configured!"
    echo "Run: aws configure"
    exit 1
fi

echo "[SUCCESS] AWS credentials configured"
echo "Account: $(aws sts get-caller-identity --query Account --output text)"
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "[WARNING] terraform.tfvars not found!"
    echo "Creating from template..."
    cp terraform.tfvars.example terraform.tfvars 2>/dev/null || true
fi

echo "========================================="
echo "Step 1: Initialize Terraform"
echo "========================================="
terraform init
echo ""

echo "========================================="
echo "Step 2: Validate Configuration"
echo "========================================="
terraform validate
echo ""

echo "========================================="
echo "Step 3: Preview Changes"
echo "========================================="
terraform plan
echo ""

echo "========================================="
echo "Ready to create infrastructure!"
echo "========================================="
echo ""
echo "Estimated time: 15-20 minutes"
echo "Estimated cost: ~$207/month"
echo ""
echo "To proceed, run:"
echo "  terraform apply"
echo ""
echo "After creation, configure kubectl with:"
echo "  aws eks update-kubeconfig --region us-east-1 --name rag-production"
echo ""
