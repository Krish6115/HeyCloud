variable "project_name" { type = string }
variable "environment" { type = string }
variable "account_id" { type = string }

variable "lifecycle_ia_days" {
  type    = number
  default = 30
}

variable "lifecycle_glacier_days" {
  type    = number
  default = 90
}

variable "lifecycle_expiration_days" {
  type    = number
  default = 365
}
