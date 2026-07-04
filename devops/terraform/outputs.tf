output "cloud_run_url" {
  description = "Public URL of the deployed CityPulse Health service"
  value       = google_cloud_run_v2_service.app.uri
}

output "artifact_registry_repo" {
  description = "Docker repo path to push images to"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}"
}

output "deployer_service_account_email" {
  description = "Service account GitHub Actions authenticates as"
  value       = google_service_account.deployer_sa.email
}

output "run_service_account_email" {
  description = "Service account the Cloud Run container runs as"
  value       = google_service_account.run_sa.email
}

output "workload_identity_provider" {
  description = "Full resource name for the GCP_WORKLOAD_IDENTITY_PROVIDER GitHub secret"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}
