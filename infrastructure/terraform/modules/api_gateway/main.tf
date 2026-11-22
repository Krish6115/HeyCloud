# =============================================================================
# Module: API Gateway
# =============================================================================
# Purpose: HTTP entry point for event ingestion and analytics queries.
# Why API Gateway:
#   - Managed, auto-scaling HTTP endpoint
#   - Built-in throttling, API keys, usage plans
#   - Direct Kinesis service integration (no Lambda proxy for ingestion)
#   - Request validation reduces invalid traffic
#   - CORS support for frontend
# =============================================================================

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "HeyCloud Real-Time Analytics Platform API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name    = "${var.project_name}-${var.environment}-api"
    Service = "apigateway"
  }
}

# -----------------------------------------------------------------------------
# /events endpoint - Direct SQS integration (replaces Kinesis PutRecord)
# -----------------------------------------------------------------------------
# The producer POSTs one JSON event to /events. API Gateway forwards the raw
# body to SQS SendMessage; the SQS -> Lambda mapping picks it up.
resource "aws_api_gateway_resource" "events" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "events"
}

resource "aws_api_gateway_method" "events_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.events.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "events_sqs" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.events.id
  http_method             = aws_api_gateway_method.events_post.http_method
  type                    = "AWS"
  integration_http_method = "POST"
  credentials             = var.api_gateway_sqs_role_arn
  uri                     = "arn:aws:apigateway:${var.aws_region}:sqs:path/${var.account_id}/${var.events_queue_name}"

  request_parameters = {
    "integration.request.header.Content-Type" = "'application/x-www-form-urlencoded'"
  }

  request_templates = {
    "application/json" = "Action=SendMessage&MessageBody=$util.urlEncode($input.body)"
  }

  passthrough_behavior = "NEVER"
}

resource "aws_api_gateway_method_response" "events_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.events.id
  http_method = aws_api_gateway_method.events_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "events_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.events.id
  http_method = aws_api_gateway_method.events_post.http_method
  status_code = aws_api_gateway_method_response.events_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  response_templates = {
    "application/json" = "{\"status\": \"accepted\"}"
  }

  depends_on = [aws_api_gateway_integration.events_sqs]
}


# -----------------------------------------------------------------------------
# /analytics endpoint - Lambda proxy
# -----------------------------------------------------------------------------
resource "aws_api_gateway_resource" "analytics" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "analytics"
}

resource "aws_api_gateway_resource" "analytics_proxy" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.analytics.id
  path_part   = "{proxy+}"
}
resource "aws_api_gateway_method" "analytics_any" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.analytics_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}


resource "aws_api_gateway_integration" "analytics_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.analytics_proxy.id
  http_method             = aws_api_gateway_method.analytics_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.analytics_api_invoke_arn
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "analytics_api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.analytics_api_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# -----------------------------------------------------------------------------
# Deployment & Stage
# -----------------------------------------------------------------------------
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.analytics_proxy.id,
      aws_api_gateway_method.analytics_any.id,
      aws_api_gateway_integration.analytics_lambda.id,
      aws_api_gateway_resource.events.id,
      aws_api_gateway_method.events_post.id,
      aws_api_gateway_integration.events_sqs.id,
      aws_api_gateway_integration_response.events_200.id,
    ]))
  }

  depends_on = [
    aws_api_gateway_integration.analytics_lambda,
    aws_api_gateway_integration.events_sqs,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  tags = {
    Name = "${var.project_name}-${var.environment}-stage"
  }
}

# API Key & Usage Plan (throttling)
resource "aws_api_gateway_api_key" "main" {
  name    = "${var.project_name}-${var.environment}-key"
  enabled = true
}

resource "aws_api_gateway_usage_plan" "main" {
  name = "${var.project_name}-${var.environment}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  throttle_settings {
    rate_limit  = var.throttle_rate_limit
    burst_limit = var.throttle_burst_limit
  }
}

resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.main.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main.id
}
