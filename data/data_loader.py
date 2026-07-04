import random
from datetime import datetime, timedelta
from google.cloud import bigquery
from who_api import fetch_and_store_who_data

PROJECT_ID = "citypulse-health-2026"
DATASET_ID = "citypulse_health"

ZONES = [
    {"zone_id": "Z01", "zone_name": "Zone 1 - North"},
    {"zone_id": "Z02", "zone_name": "Zone 2 - North East"},
    {"zone_id": "Z03", "zone_name": "Zone 3 - East"},
    {"zone_id": "Z04", "zone_name": "Zone 4 - South East"},
    {"zone_id": "Z05", "zone_name": "Zone 5 - South"},
    {"zone_id": "Z06", "zone_name": "Zone 6 - South West"},
    {"zone_id": "Z07", "zone_name": "Zone 7 - West"},
    {"zone_id": "Z08", "zone_name": "Zone 8 - North West"},
    {"zone_id": "Z09", "zone_name": "Zone 9 - Central"},
    {"zone_id": "Z10", "zone_name": "Zone 10 - District 4"},
    {"zone_id": "Z11", "zone_name": "Zone 11 - South Zone"},
    {"zone_id": "Z12", "zone_name": "Zone 12 - Outer"},
]

def generate_clinic_metrics():
    rows = []
    now = datetime.utcnow()
    for zone in ZONES:
        if zone["zone_id"] == "Z07":
            utilization = round(random.uniform(0.85, 0.95), 2)
        elif zone["zone_id"] == "Z10":
            utilization = round(random.uniform(0.90, 0.97), 2)
        else:
            utilization = round(random.uniform(0.30, 0.75), 2)

        total_beds = random.randint(40, 100)
        rows.append({
            "zone_id": zone["zone_id"],
            "zone_name": zone["zone_name"],
            "clinic_id": f"CLN-{zone['zone_id']}",
            "clinic_name": f"{zone['zone_name']} Primary Health Centre",
            "utilization_rate": utilization,
            "bed_occupancy": int(total_beds * utilization),
            "total_beds": total_beds,
            "wait_time_minutes": int(utilization * 120),
            "mobile_unit_active": random.choice([True, False]),
            "recorded_at": now.isoformat()
        })
    return rows

def generate_disease_signals(base_vaccination):
    rows = []
    now = datetime.utcnow()
    week_start = (now - timedelta(days=now.weekday())).date().isoformat()

    for zone in ZONES:
        if zone["zone_id"] == "Z07":
            dengue_risk = round(random.uniform(0.70, 0.85), 2)
            complaint_count = random.randint(80, 120)
            aqi = round(random.uniform(180, 250), 1)
            vaccination = round(base_vaccination - random.uniform(0.10, 0.20), 2)
        else:
            dengue_risk = round(random.uniform(0.05, 0.30), 2)
            complaint_count = random.randint(5, 40)
            aqi = round(random.uniform(40, 100), 1)
            vaccination = round(base_vaccination + random.uniform(-0.05, 0.05), 2)

        if zone["zone_id"] == "Z11":
            maternal = random.randint(10, 20)
        else:
            maternal = random.randint(40, 80)

        rows.append({
            "zone_id": zone["zone_id"],
            "zone_name": zone["zone_name"],
            "complaint_count": complaint_count,
            "dengue_risk_score": dengue_risk,
            "aqi": aqi,
            "vaccination_coverage": max(0.0, min(1.0, vaccination)),
            "maternal_appointments": maternal,
            "who_alert_flag": dengue_risk > 0.65,
            "week_start": week_start,
            "recorded_at": now.isoformat()
        })
    return rows

def generate_city_summary(disease_rows):
    now = datetime.utcnow()
    max_outbreak = max(r["dengue_risk_score"] for r in disease_rows)
    return [{
        "total_zones": 12,
        "signals_processed": 47,
        "outbreak_probability": round(max_outbreak, 2),
        "complaint_volume_change": round(random.uniform(0.10, 0.35), 2),
        "maternal_appointment_change": -0.40,
        "data_freshness_status": "ALL_ZONES_REPORTING",
        "summary_date": now.date().isoformat(),
        "recorded_at": now.isoformat()
    }]

def insert_rows(table_id, rows):
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        print(f"Errors inserting into {table_id}: {errors}")
    else:
        print(f"Inserted {len(rows)} rows into {table_id}")

def run():
    print("=" * 50)
    print("CityPulse Health — Data Loader")
    print("=" * 50)

    who_data = fetch_and_store_who_data()
    base_vaccination = who_data.get("WHS4_100", 85.0) / 100.0
    print(f"Using WHO vaccination coverage: {base_vaccination*100}%")
    clinic_rows = generate_clinic_metrics()
    disease_rows = generate_disease_signals(base_vaccination)
    summary_rows = generate_city_summary(disease_rows)

    insert_rows("clinic_metrics", clinic_rows)
    insert_rows("disease_signals", disease_rows)
    insert_rows("city_summary", summary_rows)

    print("=" * 50)
    print("Done. BigQuery tables populated with real + synthetic data.")
    print("=" * 50)

if __name__ == "__main__":
    run()
