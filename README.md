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
  - .github/workflows/ci.yml

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

```bash
docker compose -f devops/docker-compose.yml up --build
```

## Notes

- The current version uses sample data and placeholder agent logic.
- The coordinating agent is the main entry point for the hackathon flow.
- The app can later be extended with real city datasets and an LLM-backed response layer.
