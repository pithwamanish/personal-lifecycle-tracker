# Fix 1: The 4-minute warmer (keeps Lambda warm and Neon Postgres awake for $0)
resource "aws_cloudwatch_event_rule" "warmer" {
  name                = "${var.project_name}-warmer-${var.environment}"
  description         = "Pings /health every 4 minutes to eliminate cold starts"
  schedule_expression = var.warmer_rate
}

resource "aws_cloudwatch_event_target" "ping_warmer" {
  rule      = aws_cloudwatch_event_rule.warmer.name
  target_id = "PingHealth"
  arn       = aws_lambda_function.backend.arn
  input     = jsonencode({
    rawPath = "/health"
    requestContext = {
      http = {
        method = "GET"
        path   = "/health"
      }
    }
  })
}

resource "aws_lambda_permission" "allow_eventbridge_warmer" {
  statement_id  = "AllowExecutionFromEventBridgeWarmer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.warmer.arn
}

# Fix 4: Scheduled 08:00 AM Morning Email Digest
resource "aws_cloudwatch_event_rule" "digest" {
  name                = "${var.project_name}-daily-digest-${var.environment}"
  description         = "Triggers daily morning digest calculation at 08:00 AM UTC"
  schedule_expression = var.digest_cron
}

resource "aws_cloudwatch_event_target" "trigger_digest" {
  rule      = aws_cloudwatch_event_rule.digest.name
  target_id = "TriggerDigest"
  arn       = aws_lambda_function.backend.arn
  input     = jsonencode({
    rawPath = "/api/v1/reminders/digest/send"
    requestContext = {
      http = {
        method = "POST"
        path   = "/api/v1/reminders/digest/send"
      }
    }
  })
}

resource "aws_lambda_permission" "allow_eventbridge_digest" {
  statement_id  = "AllowExecutionFromEventBridgeDigest"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.digest.arn
}
