# Identity Cloud Run uses to actually run the container.
resource "google_service_account" "run_sa" {
  project      = var.project_id
  account_id   = "${var.service_name}-run"
  display_name = "CityPulse Health - Cloud Run runtime"

  depends_on = [google_project_service.required]
}

# Identity GitHub Actions uses to build and deploy.
resource "google_service_account" "deployer_sa" {
  project      = var.project_id
  account_id   = "${var.service_name}-deployer"
  display_name = "CityPulse Health - GitHub Actions deployer"

  depends_on = [google_project_service.required]
}

# Deployer pushes images to Artifact Registry.
resource "google_project_iam_member" "deployer_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deployer_sa.email}"
}

# Deployer creates/updates Cloud Run revisions.
resource "google_project_iam_member" "deployer_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.deployer_sa.email}"
}

# Deployer must be able to attach the runtime SA to the Cloud Run service on deploy.
resource "google_service_account_iam_member" "deployer_can_actas_run_sa" {
  service_account_id = google_service_account.run_sa.name
  role                = "roles/iam.serviceAccountUser"
  member              = "serviceAccount:${google_service_account.deployer_sa.email}"
}

# Baseline permissions the running container needs to write logs/metrics.
resource "google_project_iam_member" "run_sa_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}

resource "google_project_iam_member" "run_sa_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}

# Keyless auth: GitHub Actions exchanges its OIDC token for a short-lived
# credential impersonating deployer_sa. No JSON key ever exists (the org
# blocks SA key creation via constraints/iam.disableServiceAccountKeyCreation).
resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = var.project_id
  workload_identity_pool_id = "${var.service_name}-gh-pool"
  display_name              = "GitHub Actions pool"
  description               = "Federates GitHub Actions OIDC tokens for ${var.service_name} CI/CD"

  depends_on = [google_project_service.required]
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "${var.service_name}-gh"
  display_name                       = "GitHub provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  # Only workflow runs from this exact repo can assume the deployer identity.
  attribute_condition = "assertion.repository == \"${var.github_repo}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "wif_deployer_binding" {
  service_account_id = google_service_account.deployer_sa.name
  role                = "roles/iam.workloadIdentityUser"
  member              = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}"
}


# health_agent.py queries disease_signals/clinic_metrics/city_summary/who_indicators.
resource "google_project_iam_member" "run_sa_bigquery_data" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}

# Running a query (even read-only) requires creating a BigQuery job.
resource "google_project_iam_member" "run_sa_bigquery_job" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}

# ChatAgent/LLMClient call Gemini 2.5 Flash via Vertex AI (ADK).
resource "google_project_iam_member" "run_sa_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.run_sa.email}"
}
