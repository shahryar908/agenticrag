# =========================================
# VPC Module
# =========================================
# Creates:
# - VPC
# - Public subnets (for Load Balancers)
# - Private subnets (for EKS nodes)
# - Internet Gateway
# - NAT Gateways
# - Route tables
# =========================================

locals {
  name = "${var.cluster_name}-vpc"
}

# =========================================
# VPC
# =========================================

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    {
      Name                                        = local.name
      "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    },
    var.tags
  )
}

# =========================================
# Internet Gateway
# =========================================

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name = "${local.name}-igw"
    },
    var.tags
  )
}

# =========================================
# Public Subnets (for Load Balancers)
# =========================================

resource "aws_subnet" "public" {
  count = length(var.azs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    {
      Name                                        = "${local.name}-public-${var.azs[count.index]}"
      "kubernetes.io/role/elb"                    = "1"
      "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    },
    var.tags
  )
}

# =========================================
# Private Subnets (for EKS nodes)
# =========================================

resource "aws_subnet" "private" {
  count = length(var.azs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.azs[count.index]

  tags = merge(
    {
      Name                                        = "${local.name}-private-${var.azs[count.index]}"
      "kubernetes.io/role/internal-elb"           = "1"
      "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    },
    var.tags
  )
}

# =========================================
# Elastic IPs for NAT Gateways
# =========================================

resource "aws_eip" "nat" {
  count = length(var.azs)

  domain = "vpc"

  tags = merge(
    {
      Name = "${local.name}-nat-eip-${var.azs[count.index]}"
    },
    var.tags
  )

  depends_on = [aws_internet_gateway.main]
}

# =========================================
# NAT Gateways (for private subnet internet access)
# =========================================

resource "aws_nat_gateway" "main" {
  count = length(var.azs)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    {
      Name = "${local.name}-nat-${var.azs[count.index]}"
    },
    var.tags
  )

  depends_on = [aws_internet_gateway.main]
}

# =========================================
# Route Table for Public Subnets
# =========================================

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(
    {
      Name = "${local.name}-public-rt"
    },
    var.tags
  )
}

resource "aws_route_table_association" "public" {
  count = length(var.azs)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# =========================================
# Route Tables for Private Subnets
# =========================================

resource "aws_route_table" "private" {
  count = length(var.azs)

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge(
    {
      Name = "${local.name}-private-rt-${var.azs[count.index]}"
    },
    var.tags
  )
}

resource "aws_route_table_association" "private" {
  count = length(var.azs)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}