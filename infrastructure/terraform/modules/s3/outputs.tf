output "data_lake_bucket_name" {
  value = aws_s3_bucket.data_lake.bucket
}

output "data_lake_bucket_arn" {
  value = aws_s3_bucket.data_lake.arn
}

output "lambda_artifacts_bucket_name" {
  value = aws_s3_bucket.lambda_artifacts.bucket
}

output "lambda_artifacts_bucket_arn" {
  value = aws_s3_bucket.lambda_artifacts.arn
}
