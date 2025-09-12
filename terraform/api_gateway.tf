# === API Gateway ===
resource "aws_api_gateway_rest_api" "crossword_api" {
  name        = "crossword-api"
  description = "API Gateway for crossword lambdas"
}

# Root resource ("/")
data "aws_api_gateway_resource" "root" {
  rest_api_id = aws_api_gateway_rest_api.crossword_api.id
  path        = "/"
}

# === Endpoints for each Lambda ===

# Grid Detection Endpoint (/grid-detection)
resource "aws_api_gateway_resource" "grid_detection" {
  rest_api_id = aws_api_gateway_rest_api.crossword_api.id
  parent_id   = data.aws_api_gateway_resource.root.id
  path_part   = "grid-detection"
}

resource "aws_api_gateway_method" "grid_detection_post" {
  rest_api_id   = aws_api_gateway_rest_api.crossword_api.id
  resource_id   = aws_api_gateway_resource.grid_detection.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "grid_detection_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.crossword_api.id
  resource_id             = aws_api_gateway_resource.grid_detection.id
  http_method             = aws_api_gateway_method.grid_detection_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.grid_detection_function.invoke_arn
}

resource "aws_lambda_permission" "grid_detection_apigw" {
  statement_id  = "AllowAPIGatewayInvokeGridDetection"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.grid_detection_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.crossword_api.execution_arn}/*/POST/grid-detection"
}

# Clue Extraction Endpoint (/clue-extraction)
resource "aws_api_gateway_resource" "clue_extraction" {
  rest_api_id = aws_api_gateway_rest_api.crossword_api.id
  parent_id   = data.aws_api_gateway_resource.root.id
  path_part   = "clue-extraction"
}

resource "aws_api_gateway_method" "clue_extraction_post" {
  rest_api_id   = aws_api_gateway_rest_api.crossword_api.id
  resource_id   = aws_api_gateway_resource.clue_extraction.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "clue_extraction_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.crossword_api.id
  resource_id             = aws_api_gateway_resource.clue_extraction.id
  http_method             = aws_api_gateway_method.clue_extraction_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.clue_extraction_function.invoke_arn
}

resource "aws_lambda_permission" "clue_extraction_apigw" {
  statement_id  = "AllowAPIGatewayInvokeClueExtraction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.clue_extraction_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.crossword_api.execution_arn}/*/POST/clue-extraction"
}

# Crossword Solver Endpoint (/crossword-solver)
resource "aws_api_gateway_resource" "crossword_solver" {
  rest_api_id = aws_api_gateway_rest_api.crossword_api.id
  parent_id   = data.aws_api_gateway_resource.root.id
  path_part   = "crossword-solver"
}

resource "aws_api_gateway_method" "crossword_solver_post" {
  rest_api_id   = aws_api_gateway_rest_api.crossword_api.id
  resource_id   = aws_api_gateway_resource.crossword_solver.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "crossword_solver_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.crossword_api.id
  resource_id             = aws_api_gateway_resource.crossword_solver.id
  http_method             = aws_api_gateway_method.crossword_solver_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crossword_solver_function.invoke_arn
}

resource "aws_lambda_permission" "crossword_solver_apigw" {
  statement_id  = "AllowAPIGatewayInvokeCrosswordSolver"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.crossword_solver_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.crossword_api.execution_arn}/*/POST/crossword-solver"
}

# === Deployment & Stage ===
resource "aws_api_gateway_deployment" "crossword_api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.crossword_api.id
  depends_on = [
    aws_api_gateway_integration.grid_detection_lambda,
    aws_api_gateway_integration.clue_extraction_lambda,
    aws_api_gateway_integration.crossword_solver_lambda,
  ]
}

resource "aws_api_gateway_stage" "crossword_api_stage" {
  rest_api_id   = aws_api_gateway_rest_api.crossword_api.id
  deployment_id = aws_api_gateway_deployment.crossword_api_deployment.id
  stage_name    = "dev"
}
