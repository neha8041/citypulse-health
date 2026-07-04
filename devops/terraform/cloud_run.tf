resource "google_cloud_run_v2_service" "app" {
  project  = var.project_id
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.run_sa.email

    containers {
      # Placeholder image for the first `terraform apply`. GitHub Actions
      # overwrites this on every push to main; Terraform never touches it again.
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      env {
        name  = "APP_ENV"
        value = var.app_env
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
    ]
  }

  depends_on = [google_project_service.required]
}

# Publicly reachable so the demo link works without any auth.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
