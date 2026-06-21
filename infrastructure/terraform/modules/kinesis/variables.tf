variable "project_name" { type = string }
variable "environment" { type = string }

variable "shard_count" {
  description = "Number of shards (1 shard = 1MB/s write, 2MB/s read)"
  type        = number
  default     = 1
}

variable "retention_hours" {
  description = "Data retention period in hours"
  type        = number
  default     = 24
}
