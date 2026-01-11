# Terraform Infrastructure for RAG System

## What This Does

Automates the creation of your entire AWS infrastructure:
- VPC with public/private subnets across 3 availability zones
- EKS cluster (Kubernetes)
- Node groups (EC2 instances)
- Security groups and IAM roles
- Prometheus and Grafana monitoring
- All networking (NAT gateways, route tables, etc.)

**Before Terraform**: Manual setup takes 2-3 hours
**With Terraform**: Automated setup in 15-20 minutes

## Prerequisites

1. **AWS CLI** configured with credentials
2. **Terraform** installed (v1.0+)
3. **kubectl** installed

### Install Terraform (Windows)

```bash
# Using Chocolatey
choco install terraform

# Or download from: https://www.terraform.io/downloads
```

## Quick Start

### 1. Configure Variables

Edit `terraform.tfvars` and set your values:

```hcl
aws_region = "us-east-1"
cluster_name = "rag-production"
groq_api_key = "your-groq-api-key-here"
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

This downloads required providers (AWS, Kubernetes).

### 3. Preview Changes

```bash
terraform plan
```

This shows what will be created (no changes made yet).

### 4. Create Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will:
- Create VPC (~2 min)
- Create EKS cluster (~10-12 min)
- Create node groups (~5 min)
- Deploy monitoring (~2 min)

**Total time: 15-20 minutes**

### 5. Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name rag-production
kubectl get nodes
```

### 6. Deploy RAG Application

```bash
cd ..
kubectl apply -f k8s/
kubectl get pods -n rag-system
```

## Project Structure

```
terraform/
├── main.tf              # Main configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars     # Your values (DO NOT commit if has secrets!)
│
├── modules/
│   ├── vpc/            # VPC, subnets, NAT gateways
│   ├── eks/            # EKS cluster, node groups
│   └── monitoring/     # Prometheus, Grafana
│
└── README.md           # This file
```

## Common Commands

### View Infrastructure

```bash
# Show current state
terraform show

# List resources
terraform state list

# Show outputs
terraform output
```

### Update Infrastructure

```bash
# After changing variables
terraform plan
terraform apply
```

### Destroy Infrastructure

```bash
# Delete everything (saves money when not in use)
terraform destroy
```

**WARNING**: This deletes the entire cluster and all data!

## Configuration Options

### Change Region

Edit `terraform.tfvars`:
```hcl
aws_region = "eu-west-1"
```

### Scale Nodes

```hcl
node_desired_size = 3  # Increase from 2 to 3
node_max_size = 6      # Increase max
```

### Enable Spot Instances (70% cheaper)

```hcl
enable_spot_instances = true
```

**Trade-off**: Spot instances can be interrupted by AWS.

### Disable Monitoring

```hcl
enable_prometheus = false
enable_grafana = false
```

**Saves**: ~$20/month

## Cost Breakdown

| Resource | Cost/Month | Notes |
|----------|-----------|-------|
| EKS Control Plane | $75 | Fixed cost |
| 2x t3.medium nodes | $70 | $35 each |
| NAT Gateways | $32 | $0.045/hour x 2 |
| Load Balancer | $20 | For services |
| EBS Storage | $10 | 20GB per node |
| **Total** | **~$207/month** | |

### Cost Optimization Tips

1. **Use Spot Instances**: Save 70% on nodes
2. **Single NAT Gateway**: Save $16/month (less HA)
3. **Smaller nodes**: Use t3.small instead of t3.medium
4. **Auto-shutdown**: Destroy when not in use

**Optimized cost**: ~$80-100/month

## Remote State (Production)

For team collaboration, store state in S3:

### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-terraform-state-bucket
```

### 2. Enable in main.tf

Uncomment the backend block:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "rag-system/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

### 3. Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Troubleshooting

### Error: "Error creating EKS Cluster"

**Cause**: IAM permissions or quota limits

**Fix**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check EKS quota
aws service-quotas list-service-quotas \
  --service-code eks
```

### Error: "Insufficient capacity"

**Cause**: AWS doesn't have t3.medium capacity in that AZ

**Fix**: Change instance type or region
```hcl
node_instance_types = ["t3a.medium", "t3.small"]
```

### State Lock Error

**Cause**: Previous terraform command crashed

**Fix**:
```bash
terraform force-unlock <LOCK_ID>
```

## Security Best Practices

### 1. Don't Commit Secrets

Add to `.gitignore`:
```
terraform.tfvars
*.tfstate
*.tfstate.backup
.terraform/
```

### 2. Use Environment Variables

```bash
export TF_VAR_groq_api_key="your-key"
terraform apply
```

### 3. Enable Encryption

Already enabled by default:
- EBS volumes encrypted
- Secrets encrypted at rest
- HTTPS for all endpoints

## What You're Learning

- **Infrastructure as Code**: Reproducible infrastructure
- **AWS**: VPC, EKS, IAM, Security Groups
- **Terraform**: Modules, state management, providers
- **DevOps**: Automation, version control
- **Kubernetes**: Integration with cloud providers

## Interview Questions

**Q: Why use Terraform instead of manual setup?**
A: Terraform provides reproducible, version-controlled infrastructure. I can create identical environments (dev/staging/prod) in minutes, and changes are tracked in Git.

**Q: How do you handle state management?**
A: For production, I use S3 backend with DynamoDB for state locking. This enables team collaboration and prevents concurrent modifications.

**Q: How do you manage secrets in Terraform?**
A: I use environment variables (TF_VAR_*) for sensitive values and never commit terraform.tfvars. In production, I'd use AWS Secrets Manager or HashiCorp Vault.

**Q: What's your process for infrastructure changes?**
A: Always run `terraform plan` first to review changes, test in dev environment, then apply to staging, and finally to production with approval.

**Q: How do you handle disaster recovery?**
A: Terraform state is backed up in S3 with versioning. I can recreate the entire infrastructure by running `terraform apply` from version control.

## Next Steps

After Terraform is working:

1. **Add GitOps**: Use ArgoCD for application deployment
2. **Add Logging**: ELK stack or CloudWatch Logs
3. **Add Alerts**: AlertManager with Slack/PagerDuty
4. **Add Auto-scaling**: HPA for pods, Cluster Autoscaler for nodes
5. **Add CI/CD**: Integrate Terraform into GitHub Actions

## Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)

---

**Your infrastructure is now fully automated and production-ready!**
