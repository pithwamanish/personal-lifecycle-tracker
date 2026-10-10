data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "random_password" "postgres_pwd" {
  length  = 24
  special = false
}

locals {
  db_password = var.postgres_password != "" ? var.postgres_password : random_password.postgres_pwd.result
  ami_id      = var.ami_id != null ? var.ami_id : data.aws_ami.ubuntu.id
}

resource "aws_instance" "app" {
  ami                    = local.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  key_name               = var.key_name

  user_data = templatefile("${path.module}/user_data.sh", {
    APP_PORT          = var.app_port
    REPO_URL          = var.repo_url
    REPO_BRANCH       = var.repo_branch
    POSTGRES_PASSWORD = local.db_password
    ENVIRONMENT       = var.environment
  })

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name        = "${var.project_name}-root-volume-${var.environment}"
      Environment = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-ec2-${var.environment}"
    Environment = var.environment
  }
}
