locals {
  create_oidc_provider = var.enable_github_oidc && var.existing_oidc_provider_arn == null
  oidc_provider_arn    = var.existing_oidc_provider_arn != null ? var.existing_oidc_provider_arn : (length(aws_iam_openid_connect_provider.github_actions) > 0 ? aws_iam_openid_connect_provider.github_actions[0].arn : "")
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  count = local.create_oidc_provider ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f8d264fcd9"
  ]

  tags = {
    Name        = "${var.project_name}-github-oidc-provider"
    Environment = var.environment
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "github_actions_render_deployer" {
  count = var.enable_github_oidc ? 1 : 0

  name = "${var.project_name}-github-oidc-render-deployer-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = local.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-github-oidc-render-deployer-${var.environment}"
    Environment = var.environment
  }
}

# Policy allowing the GitHub Actions OIDC role to read Render deployment secrets
resource "aws_iam_policy" "render_secrets_reader" {
  count = var.enable_github_oidc ? 1 : 0

  name        = "${var.project_name}-render-secrets-policy-${var.environment}"
  description = "Allows GitHub Actions OIDC role to read Render deployment credentials (${var.environment})"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:personal-lifecycle/render*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/personal-lifecycle/render/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_render_secrets" {
  count = var.enable_github_oidc ? 1 : 0

  role       = aws_iam_role.github_actions_render_deployer[0].name
  policy_arn = aws_iam_policy.render_secrets_reader[0].arn
}

# Policy allowing the GitHub Actions OIDC role to push images to ECR and manage deployment parameters
resource "aws_iam_policy" "github_actions_ecr_deploy" {
  count = var.enable_github_oidc ? 1 : 0

  name        = "${var.project_name}-ecr-deploy-policy-${var.environment}"
  description = "Allows GitHub Actions OIDC role to push and pull ECR images and manage deployment parameters"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:DescribeImages",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
          "ecr:CreateRepository"
        ]
        Resource = [
          "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${var.project_name}*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:PutParameter",
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/personal-lifecycle/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_ecr_deploy" {
  count = var.enable_github_oidc ? 1 : 0

  role       = aws_iam_role.github_actions_render_deployer[0].name
  policy_arn = aws_iam_policy.github_actions_ecr_deploy[0].arn
}

