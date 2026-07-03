# CityPulse Health

CityPulse Health is an AI-powered public health briefing assistant for city officials. The project is scaffolded as a Python application with a modular, agent-based architecture for the hackathon demo.

## Project Structure

- app/ - main Python application package
  - app/agents/ - agent modules for the system
    - base_agent.py - shared base class for all agents
    - morning_briefing_agent.py - creates the morning health summary
    - data_query_agent.py - handles follow-up data questions
    - action_agent.py - drafts recommended actions
    - coordinating_agent.py - main orchestrator for the agent workflow
  - app/services/ - supporting services
    - data_loader.py - loads sample city health data
    - llm_client.py - placeholder integration point for future LLM use
  - app/workflows/ - workflow orchestration
    - morning_briefing.py - runs the end-to-end briefing flow
  - app/models/ - domain models
    - health_signal.py - health signal data structure
  - app/config.py - environment-based configuration
  - app/main.py - FastAPI app entry point
- data/ - raw and processed datasets
- tests/ - starter test files
- devops/ - deployment and infrastructure support
  - Dockerfile
  - docker-compose.yml
  - scripts/run_app.sh
  - terraform/ - GCP infra (Cloud Run, Artifact Registry, service accounts/IAM)
- .github/workflows/deploy.yml - CI/CD: tests on every push/PR, deploys to Cloud Run on push to `main`

## How to Run

### 1. Create a Python environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the app

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/briefing
```

### 4. Run with Docker (optional)

Requires a `.env` file at the repo root (`cp .env.example .env`) — Compose loads it directly.

```bash
docker compose -f devops/docker-compose.yml up --build
```

## Notes

- The current version uses sample data and placeholder agent logic.
- The coordinating agent is the main entry point for the hackathon flow.
- The app can later be extended with real city datasets and an LLM-backed response layer.

## Deployment (Google Cloud Run)

Every push to `main` automatically builds a container image and deploys it to Cloud Run
via `.github/workflows/deploy.yml`. Every push/PR also runs the test suite.

### One-time setup

1. **Set your Terraform variables.** Nothing account-specific is hardcoded in any
   `.tf` file — copy the example and fill in your own values (this file is
   gitignored, it never gets committed):

   ```bash
   cd devops/terraform
   cp terraform.tfvars.example terraform.tfvars
   # edit terraform.tfvars: project_id, region, service_name, repo_name, github_repo
   ```

   (Equivalently, skip the file and export `TF_VAR_project_id`, `TF_VAR_region`, etc.)

2. **Provision GCP infra** (Artifact Registry, the Cloud Run service, both service
   accounts, all IAM role bindings, and the Workload Identity Federation pool):

   ```bash
   terraform init
   terraform apply
   ```

3. **Read the outputs** — these become your GitHub configuration in the next step:

   ```bash
   terraform output -raw workload_identity_provider
   terraform output -raw deployer_service_account_email
   ```

4. **Configure GitHub.** Non-secret config goes under Settings → Secrets and
   variables → Actions → **Variables**; anything credential-shaped goes under
   **Secrets**. Values must match what you put in `terraform.tfvars`.

   | Variable | Value |
   |---|---|
   | `GCP_PROJECT_ID` | your `project_id` |
   | `GCP_REGION` | your `region` |
   | `GCP_SERVICE_NAME` | your `service_name` |
   | `GCP_REPO_NAME` | your `repo_name` |
   | `MODEL_NAME` | optional, defaults to `gpt-4o-mini` |
   | `APP_ENV` | optional, defaults to `production` |

   | Secret | Value |
   |---|---|
   | `GCP_WORKLOAD_IDENTITY_PROVIDER` | output of `workload_identity_provider` |
   | `GCP_SERVICE_ACCOUNT` | output of `deployer_service_account_email` |
   | `OPENAI_API_KEY` | your OpenAI key (same value as in your local `.env`) |

5. Push to `main`. The `deploy` job builds the image, pushes it to Artifact
   Registry, and runs `gcloud run deploy`. The job's last step prints the
   public Cloud Run URL — that link is the live demo.

### How credentials flow

- Locally: copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`. `app/config.py`
  loads it via `python-dotenv`, and `devops/docker-compose.yml` loads the same file via
  `env_file`. `.env` is gitignored and never committed.
- In Terraform: account-specific values (project, region, names, GitHub repo) live only
  in `terraform.tfvars`, which is gitignored — `devops/terraform/*.tf` contains no
  hardcoded project IDs or account names, only variable references.
- In CI/CD: `.github/workflows/deploy.yml` reads GCP project/region/service/repo names
  from `vars.*` (GitHub Actions Variables) and credentials from `secrets.*` — none of
  it is hardcoded in the workflow file. Values are passed to the container with
  `--update-env-vars` on every `gcloud run deploy`.
- Auth to GCP: GitHub Actions never holds a GCP credential at rest. Each workflow
  run presents its OIDC token to the Workload Identity Pool (`devops/terraform/service_accounts.tf`),
  which is only trusted for tokens whose `repository` claim equals your configured
  `github_repo`, and exchanges it for a short-lived token impersonating the deployer
  service account.
- IAM: all roles (Artifact Registry writer, Cloud Run admin, service-account-user,
  logging/monitoring writer, workload-identity-user) are defined in
  `devops/terraform/service_accounts.tf` — there is no manual IAM setup in the GCP console.
