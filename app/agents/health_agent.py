import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.cloud import bigquery

PROJECT_ID = "citypulse-health-2026"
DATASET_ID = "citypulse_health"
LOCATION = "us-central1"

os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

bq_client = bigquery.Client(project=PROJECT_ID)

# ─────────────────────────────────────────────
# TOOLS — functions the agent can call
# ─────────────────────────────────────────────

def get_zone_health_status(zone_id: str) -> dict:
    """Get the latest health status for a specific zone including
    dengue risk, clinic utilization and maternal care data."""
    query = f"""
        WITH latest_disease AS (
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY zone_id ORDER BY recorded_at DESC) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.disease_signals`
            ) WHERE rn = 1
        ),
        latest_clinic AS (
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY zone_id ORDER BY recorded_at DESC) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.clinic_metrics`
            ) WHERE rn = 1
        )
        SELECT
            d.zone_id,
            d.zone_name,
            d.dengue_risk_score,
            d.complaint_count,
            d.maternal_appointments,
            d.aqi,
            d.vaccination_coverage,
            c.utilization_rate,
            c.wait_time_minutes,
            c.total_beds,
            c.bed_occupancy
        FROM latest_disease d
        JOIN latest_clinic c ON d.zone_id = c.zone_id
        WHERE d.zone_id = '{zone_id}'
    """
    results = bq_client.query(query).result()
    rows = [dict(row) for row in results]
    if not rows:
        return {"error": f"Zone {zone_id} not found"}
    r = rows[0]
    return {
        "zone_id": r["zone_id"],
        "zone_name": r["zone_name"],
        "dengue_outbreak_probability": f"{int(r['dengue_risk_score']*100)}%",
        "citizen_complaints_this_week": r["complaint_count"],
        "aqi": r["aqi"],
        "vaccination_coverage": f"{int(r['vaccination_coverage']*100)}%",
        "clinic_utilization": f"{int(r['utilization_rate']*100)}%",
        "wait_time_minutes": r["wait_time_minutes"],
        "beds_occupied": f"{r['bed_occupancy']} of {r['total_beds']}",
        "maternal_appointments_this_week": r["maternal_appointments"]
    }

def get_all_zones_summary() -> dict:
    """Get a summary of all 12 zones ranked by risk level."""
    query = f"""
        WITH latest_disease AS (
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY zone_id ORDER BY recorded_at DESC) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.disease_signals`
            ) WHERE rn = 1
        ),
        latest_clinic AS (
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY zone_id ORDER BY recorded_at DESC) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.clinic_metrics`
            ) WHERE rn = 1
        )
        SELECT
            d.zone_id,
            d.zone_name,
            d.dengue_risk_score,
            d.complaint_count,
            c.utilization_rate,
            d.maternal_appointments
        FROM latest_disease d
        JOIN latest_clinic c ON d.zone_id = c.zone_id
        ORDER BY d.dengue_risk_score DESC
    """
    results = bq_client.query(query).result()
    zones = []
    for row in results:
        r = dict(row)
        zones.append({
            "zone_id": r["zone_id"],
            "zone_name": r["zone_name"],
            "dengue_risk": f"{int(r['dengue_risk_score']*100)}%",
            "complaints": r["complaint_count"],
            "clinic_utilization": f"{int(r['utilization_rate']*100)}%",
            "maternal_appointments": r["maternal_appointments"]
        })
    return {"total_zones": len(zones), "zones": zones}

def get_anomalies() -> dict:
    """Detect and return all current health anomalies across the city."""
    query = f"""
        WITH latest_disease AS (
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY zone_id ORDER BY recorded_at DESC) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.disease_signals`
            ) WHERE rn = 1
        ),
        latest_clinic AS (
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY zone_id ORDER BY recorded_at DESC) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.clinic_metrics`
            ) WHERE rn = 1
        )
        SELECT
            d.zone_id,
            d.zone_name,
            d.dengue_risk_score,
            d.complaint_count,
            d.maternal_appointments,
            d.aqi,
            c.utilization_rate,
            c.wait_time_minutes
        FROM latest_disease d
        JOIN latest_clinic c ON d.zone_id = c.zone_id
        WHERE d.dengue_risk_score > 0.65
           OR c.utilization_rate > 0.88
           OR d.maternal_appointments < 25
        ORDER BY d.dengue_risk_score DESC
    """
    results = bq_client.query(query).result()
    anomalies = []
    for row in results:
        r = dict(row)
        if r["dengue_risk_score"] > 0.65:
            anomalies.append({
                "type": "DENGUE_RISK",
                "zone": r["zone_name"],
                "dengue_outbreak_probability": f"{int(r['dengue_risk_score']*100)}%",
                "complaints": r["complaint_count"],
                "aqi": r["aqi"]
            })
        if r["utilization_rate"] > 0.88:
            anomalies.append({
                "type": "CLINIC_OVERLOAD",
                "zone": r["zone_name"],
                "utilization": f"{int(r['utilization_rate']*100)}%",
                "wait_time_minutes": r["wait_time_minutes"]
            })
        if r["maternal_appointments"] < 25:
            anomalies.append({
                "type": "MATERNAL_CARE_DROP",
                "zone": r["zone_name"],
                "appointments_this_week": r["maternal_appointments"],
                "drop_percentage": f"{int((1 - r['maternal_appointments']/55)*100)}%"
            })
    return {"anomaly_count": len(anomalies), "anomalies": anomalies}

def get_city_summary() -> dict:
    """Get the overall city health summary for today."""
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.city_summary`
        ORDER BY recorded_at DESC
        LIMIT 1
    """
    results = bq_client.query(query).result()
    rows = [dict(row) for row in results]
    if not rows:
        return {"error": "No city summary found"}
    r = rows[0]
    return {
        "date": str(r["summary_date"]),
        "total_zones_monitored": r["total_zones"],
        "signals_processed_overnight": r["signals_processed"],
        "highest_outbreak_probability": f"{int(r['outbreak_probability']*100)}%",
        "complaint_volume_change": f"+{int(r['complaint_volume_change']*100)}%",
        "maternal_appointment_change": f"{int(r['maternal_appointment_change']*100)}%",
        "data_freshness": r["data_freshness_status"]
    }

def draft_field_alert(zone_id: str, issue_type: str) -> dict:
    """Draft a field team alert for a specific zone and issue type.
    issue_type can be DENGUE_RISK, CLINIC_OVERLOAD, or MATERNAL_CARE_DROP."""
    zone_status = get_zone_health_status(zone_id)
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

Your tools:
- get_city_summary: get overall city health status
- get_all_zones_summary: get all zones ranked by risk
- get_zone_health_status: get detailed status for a specific zone
- get_anomalies: detect all current health anomalies
- draft_field_alert: draft an alert for field teams

Your behaviour:
- Always use tools to fetch real data before answering
- Speak in plain English, not technical jargon
- Use percentages not decimals (79% not 0.79)
- Be specific — name zones, give numbers
- For anomalies always recommend a concrete action
- For the morning briefing: call get_anomalies and get_city_summary together
- Keep responses concise and actionable
"""

def create_agent():
    agent = Agent(
        name="citypulse_health_agent",
        model="gemini-2.5-flash",
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
    import asyncio
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

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
