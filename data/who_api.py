from datetime import datetime
import requests
from google.cloud import bigquery

WHO_BASE = "https://ghoapi.azureedge.net/api"
PROJECT_ID = "citypulse-health-2026"
DATASET_ID = "citypulse_health"

bq_client = bigquery.Client(project=PROJECT_ID)

def fetch_and_store_who_data():
    """Fetch real WHO indicators for India and store in BigQuery"""
    indicators = [
        {
            "code": "WHS4_100",
            "name": "DTP3 immunization coverage among 1-year-olds (%)",
            "unit": "thousands"
        },
        {
            "code": "MALARIA_EST_DEATHS",
            "name": "Malaria estimated deaths",
            "unit": "count"
        },
        {
            "code": "MDG_0000000026",
            "name": "Neonatal mortality rate per 1000 live births",
            "unit": "rate"
        },
        {
            "code": "NUTRITION_ANAEMIA_PREGNANT_NUM",
            "name": "Number of pregnant women with anaemia (thousands)",
            "unit": "thousands"
        }
    ]

    rows = []
    now = datetime.utcnow().isoformat()

    for indicator in indicators:
        print(f"Fetching WHO data: {indicator['name']}...")
        query_params = "?$filter=SpatialDim eq 'IND'&$orderby=TimeDim desc&$top=1"
        url = f"{WHO_BASE}/{indicator['code']}{query_params}"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if data.get("value"):
                latest = data["value"][0]
                value = latest.get("NumericValue")
                year = latest.get("TimeDim")
                if value is not None:
                    rows.append({
                        "indicator_code": indicator["code"],
                        "indicator_name": indicator["name"],
                        "country": "IND",
                        "year": int(year),
                        "value": float(value),
                        "unit": indicator["unit"],
                        "recorded_at": now
                    })
                    print(f"  Got: {value} ({year})")
                else:
                    print("  No value found")
            else:
                print("  No data returned")
        except Exception as e:
            print(f"  Error: {e}")

    if rows:
        errors = bq_client.insert_rows_json(
            f"{PROJECT_ID}.{DATASET_ID}.who_indicators",
            rows
        )
        if errors:
            print(f"BigQuery insert errors: {errors}")
        else:
            print(f"\nStored {len(rows)} WHO indicators in BigQuery")

    # Return as dict keyed by indicator code for easy lookup
    result = {}
    for r in rows:
        result[r["indicator_code"]] = r["value"]
    return result

def fetch_vaccination_coverage_india():
    """Fetch real DTP3 vaccination coverage for India from WHO"""
    url = f"{WHO_BASE}/WHS4_100?$filter=SpatialDim eq 'IND'&$orderby=TimeDim desc&$top=1"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("value"):
            latest = data["value"][0]
            coverage = latest.get("NumericValue", 85.0)
            year = latest.get("TimeDim", 2023)
            print(f"WHO: India DTP3 vaccination coverage = {coverage}% (year {year})")
            return float(coverage) / 100.0
        return 0.85
    except Exception as e:
        print(f"WHO API error: {e} — using fallback 85%")
        return 0.85

if __name__ == "__main__":
    print("=" * 50)
    print("WHO Data Fetch and Store")
    print("=" * 50)
    rows = fetch_and_store_who_data()
    print("\nStored indicators:")
    for r in rows:
        print(f"  {r['indicator_name']}: {r['value']} {r['unit']} ({r['year']})")
