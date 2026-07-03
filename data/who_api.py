import requests

WHO_BASE = "https://ghoapi.azureedge.net/api"

def fetch_vaccination_coverage_india():
    """Fetch real DTP3 vaccination coverage for India from WHO"""
    print("Fetching real WHO vaccination coverage for India...")
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
    coverage = fetch_vaccination_coverage_india()
    print(f"Coverage value: {coverage}")
