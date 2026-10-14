# Live AWS SNS -> Lambda On-Call Incident Responder Infrastructure

resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts-${var.environment}"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Component   = "Observability-OnCall"
  }
}

# CloudWatch Metric Alarm triggering on Lambda errors
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${var.project_name}-api-5xx-alarm-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Elevated 5xx error rate detected on backend API"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.backend.function_name
  }
}

# Archive file packaging the on-call responder Python handler
data "archive_file" "on_call_responder_zip" {
  type        = "zip"
  source_file = "${path.module}/../../on-call-engineer/lambda_handler.py"
  output_path = "${path.module}/on-call-responder.zip"
}

# IAM Role for On-Call Responder Lambda
resource "aws_iam_role" "on_call_responder" {
  name = "${var.project_name}-on-call-responder-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "on_call_basic" {
  role       = aws_iam_role.on_call_responder.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "on_call_remediation" {
  name = "${var.project_name}-on-call-remediation-policy-${var.environment}"
  role = aws_iam_role.on_call_responder.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaOperationalRemediation"
        Effect = "Allow"
        Action = [
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:UpdateFunctionConfiguration",
          "lambda:UpdateFunctionCode",
          "lambda:PublishVersion",
          "lambda:ListVersionsByFunction"
        ]
        Resource = aws_lambda_function.backend.arn
      },
      {
        Sid    = "AllowCloudWatchAlarmInspection"
        Effect = "Allow"
        Action = [
          "cloudwatch:DescribeAlarms",
          "cloudwatch:GetMetricData",
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group for On-Call Responder
resource "aws_cloudwatch_log_group" "on_call_logs" {
  name              = "/aws/lambda/${var.project_name}-on-call-responder-${var.environment}"
  retention_in_days = 14
}

# On-Call Responder Lambda Function
resource "aws_lambda_function" "on_call_responder" {
  function_name    = "${var.project_name}-on-call-responder-${var.environment}"
  role             = aws_iam_role.on_call_responder.arn
  runtime          = "python3.11"
  handler          = "lambda_handler.lambda_handler"
  filename         = data.archive_file.on_call_responder_zip.output_path
  source_code_hash = data.archive_file.on_call_responder_zip.output_base64sha256
  memory_size      = 256
  timeout          = 60

  environment {
    variables = {
      APP_ENV              = var.environment
      TARGET_FUNCTION_NAME = aws_lambda_function.backend.function_name
      HEALTH_ENDPOINT_URL  = aws_lambda_function_url.backend_url.function_url
      AUTONOMY_LEVEL       = "LEVEL_1_AUTO_EXECUTE"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.on_call_logs
  ]
}

# Allow SNS to invoke On-Call Responder
resource "aws_lambda_permission" "allow_sns_invoke_responder" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.on_call_responder.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alerts.arn
}

# SNS Subscription wiring the alerts topic to the on-call responder
resource "aws_sns_topic_subscription" "alerts_to_on_call" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.on_call_responder.arn
}

# Outputs for live on-call infrastructure
output "on_call_sns_topic_arn" {
  description = "Amazon SNS Topic ARN for incident response alerts"
  value       = aws_sns_topic.alerts.arn
}

output "on_call_responder_function_name" {
  description = "AWS Lambda on-call responder function name"
  value       = aws_lambda_function.on_call_responder.function_name
}
