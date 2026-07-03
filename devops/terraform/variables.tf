# No defaults on purpose: every account-specific value is supplied via
# terraform.tfvars (gitignored, see terraform.tfvars.example) or TF_VAR_*
# environment variables — never hardcoded into a committed .tf file.

variable "project_id" {
  description = "GCP project ID to deploy into"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run and Artifact Registry"
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "repo_name" {
  description = "Artifact Registry repository name"
  type        = string
}

variable "github_repo" {
  description = "GitHub repo allowed to assume the deployer identity, as 'owner/name'"
  type        = string
}

variable "app_env" {
  description = "Value for the APP_ENV environment variable on Cloud Run"
  type        = string
  default     = "production"
}
