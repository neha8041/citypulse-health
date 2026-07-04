resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repo_name
  format        = "DOCKER"
  description   = "Docker images for CityPulse Health"

  depends_on = [google_project_service.required]
}
