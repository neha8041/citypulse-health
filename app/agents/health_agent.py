import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.services.health_repository import HealthRepository
from app.core.config import logger, PROJECT_ID, MODEL_NAME

LOCATION = "us-central1"

os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

_REPO = None

def get_repo() -> HealthRepository:
    # pylint: disable=global-statement
    global _REPO
    if _REPO is None:
        _REPO = HealthRepository()
    return _REPO

# ─────────────────────────────────────────────
# TOOLS — functions the agent can call
# ─────────────────────────────────────────────

async def get_zone_health_status(zone_id: str) -> dict:
    """Get the latest health status for a specific zone including
    dengue risk, clinic utilization and maternal care data."""
    logger.info("Agent executing tool: get_zone_health_status(%s)", zone_id)
    return await get_repo().get_zone_health_status(zone_id)

async def get_all_zones_summary() -> list:
    """Get a summary of all zones ranked by risk level. 
    Use this to identify which zones need the most urgent attention."""
    logger.info("Agent executing tool: get_all_zones_summary")
    return await get_repo().get_all_zones_summary()

async def get_anomalies(risk_threshold: float = 0.7) -> list:
    """Get all zones where the dengue risk score is above the given threshold.
    Default threshold is 0.70."""
    logger.info("Agent executing tool: get_anomalies(threshold=%s)", risk_threshold)
    return await get_repo().get_anomalies(risk_threshold)

async def get_city_summary() -> dict:
    """Get the overall city health status including average risk
    and total resources deployed."""
    logger.info("Agent executing tool: get_city_summary")
    return await get_repo().get_city_summary()

async def draft_field_alert(zone_id: str, issue_type: str) -> dict:
    """Draft a field team alert for a specific zone and issue type.
    issue_type can be DENGUE_RISK, CLINIC_OVERLOAD, or MATERNAL_CARE_DROP."""
    logger.info(
        "Agent executing tool: draft_field_alert(zone_id=%s, issue_type=%s)",
        zone_id, issue_type
    )
    zone_status = await get_zone_health_status(zone_id)
    if "error" in zone_status:
        return zone_status

    templates = {
        "DENGUE_RISK": f"""
URGENT FIELD ALERT — DENGUE RISK
Zone: {zone_status['zone_name']}
Date: {zone_status.get('date', 'Today')}

Dengue outbreak probability has reached {zone_status['dengue_outbreak_probability']} in your zone.
Citizen complaints this week: {zone_status['citizen_complaints_this_week']}
Current AQI: {zone_status['aqi']} (hazardous)

Required actions:
1. Deploy vector control teams immediately
2. Set up rapid dengue testing at the PHC
3. Distribute mosquito nets and repellents to high-density areas
4. Begin daily reporting to district health office

Report status to command by 6 PM today.
""",
        "CLINIC_OVERLOAD": f"""
FIELD ALERT — CLINIC CAPACITY CRITICAL
Zone: {zone_status['zone_name']}

Clinic utilization has reached {zone_status['clinic_utilization']}.
Current wait time: {zone_status['wait_time_minutes']} minutes.

Required actions:
1. Redirect non-critical cases to Zone 2 (34% utilization)
2. Request additional staff from district pool
3. Open extended hours from 8 PM to 10 PM this week
4. Set up triage point outside clinic entrance

Report headcount every 4 hours.
""",
        "MATERNAL_CARE_DROP": f"""
FIELD ALERT — MATERNAL CARE ACCESS GAP
Zone: {zone_status['zone_name']}

Maternal care appointments dropped to {zone_status['maternal_appointments_this_week']} this week.
This is a significant drop requiring immediate community outreach.

Required actions:
1. Contact ASHA workers in the zone for door-to-door outreach
2. Check if transport barriers are preventing visits
3. Open Saturday maternal care clinic this weekend
4. Report barriers identified by end of week

This is time-sensitive — maternal health outcomes depend on timely care.
"""
    }

    alert = templates.get(issue_type, "Unknown issue type")
    return {
        "zone": zone_status["zone_name"],
        "issue_type": issue_type,
        "alert_draft": alert,
        "status": "READY_TO_SEND"
    }

# ─────────────────────────────────────────────
# ADK AGENT
# ─────────────────────────────────────────────

AGENT_INSTRUCTION = """
You are CityPulse, an AI health intelligence agent for a city health official.
You have access to real-time health data across 12 zones in the city.
You are the CityPulse Health Coordinator Agent.
You have access to real-time health signals from BigQuery across 12 city zones.
Your job is to answer queries from health officials and draft field alerts.

Rules:
- Always fetch the latest data before answering
- If an anomaly is detected, proactively suggest actions
- Maintain a professional, urgent tone for alerts
- Keep responses concise and actionable
"""

def create_agent():
    agent = Agent(
        name="citypulse_health_agent",
        model=MODEL_NAME,
        description="City health intelligence agent for monitoring and decision support",
        instruction=AGENT_INSTRUCTION,
        tools=[
            get_zone_health_status,
            get_all_zones_summary,
            get_anomalies,
            get_city_summary,
            draft_field_alert
        ]
    )
    return agent

async def run_agent(user_message: str):
    """Run the agent with a user message and return the response"""
    logger.info("Starting agent session for message: '%s'", user_message)

    session_service = InMemorySessionService()
    agent = create_agent()
    runner = Runner(
        agent=agent,
        app_name="citypulse_health",
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name="citypulse_health",
        user_id="health_official"
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    )

    final_response = ""
    async for event in runner.run_async(
        user_id="health_official",
        session_id=session.id,
        new_message=content
    ):
        if event.is_final_response():
            final_response = event.content.parts[0].text

    logger.info("Agent session completed")
    return final_response

if __name__ == "__main__":
    import asyncio

    print("=" * 50)
    print("CityPulse Health Agent — ADK")
    print("=" * 50)

    # Test 1: Morning briefing
    print("\nTEST 1: Generate morning briefing")
    print("-" * 40)
    response = asyncio.run(run_agent(
        "Generate the morning briefing for today. Check all anomalies and give me a summary."
    ))
    print(response)

    # Test 2: Specific zone query
    print("\nTEST 2: Zone 7 drill down")
    print("-" * 40)
    response = asyncio.run(run_agent(
        "Give me the detailed health status for zone Z07"
    ))
    print(response)

    # Test 3: Draft an alert
    print("\nTEST 3: Draft field alert for Zone 7")
    print("-" * 40)
    response = asyncio.run(run_agent(
        "Draft a field team alert for the dengue risk in zone Z07"
    ))
    print(response)
