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
# /events endpoint - Direct Kinesis integration
# -----------------------------------------------------------------------------


# Direct integration with Kinesis PutRecord (no Lambda proxy)
# CORS preflight for /events


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
    ]))
  }

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
