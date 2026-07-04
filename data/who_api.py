"""Fetch and store WHO health data asynchronously."""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from google.cloud import bigquery

from app.core.config import DATASET_ID, PROJECT_ID, logger

WHO_BASE = "https://ghoapi.azureedge.net/api"


async def fetch_indicator(
    client: httpx.AsyncClient, indicator: Dict[str, str], now: str
) -> Optional[Dict[str, Any]]:
    """Fetch a single indicator from WHO API concurrently."""
    query_params = "?$filter=SpatialDim eq 'IND'&$orderby=TimeDim desc&$top=1"
    url = f"{WHO_BASE}/{indicator['code']}{query_params}"

    logger.info("Fetching WHO data: %s...", indicator["name"])
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        if data.get("value"):
            latest = data["value"][0]
            value = latest.get("NumericValue")
            year = latest.get("TimeDim")

            if value is not None:
                logger.info("  Got: %s (%s) for %s", value, year, indicator["code"])
                return {
                    "indicator_code": indicator["code"],
                    "indicator_name": indicator["name"],
                    "country": "IND",
                    "year": int(year),
                    "value": float(value),
                    "unit": indicator["unit"],
                    "recorded_at": now,
                }
            logger.warning("  No value found for %s", indicator["code"])
        else:
            logger.warning("  No data returned for %s", indicator["code"])
    except Exception as e:
        logger.error("  Error fetching %s: %s", indicator["code"], e)

    return None


async def fetch_all_indicators() -> List[Dict[str, Any]]:
    """Gather multiple WHO indicators concurrently."""
    indicators = [
        {"code": "WHS4_100", "name": "DTP3 immunization coverage", "unit": "thousands"},
        {"code": "MALARIA_EST_DEATHS", "name": "Malaria estimated deaths", "unit": "count"},
        {"code": "MDG_0000000026", "name": "Neonatal mortality rate", "unit": "rate"},
        {"code": "NUTRITION_ANAEMIA_PREGNANT_NUM",
         "name": "Pregnant women with anaemia", "unit": "thousands"},
    ]
    now = datetime.utcnow().isoformat()

    async with httpx.AsyncClient() as client:
        tasks = [fetch_indicator(client, ind, now) for ind in indicators]
        results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]


def fetch_and_store_who_data() -> Dict[str, float]:
    """Synchronous wrapper for data loader to insert into BigQuery."""
    rows = asyncio.run(fetch_all_indicators())

    if rows:
        bq_client = bigquery.Client(project=PROJECT_ID)
        errors = bq_client.insert_rows_json(
            f"{PROJECT_ID}.{DATASET_ID}.who_indicators", rows
        )
        if errors:
            logger.error("BigQuery insert errors: %s", errors)
        else:
            logger.info("Stored %d WHO indicators in BigQuery", len(rows))

    result = {r["indicator_code"]: r["value"] for r in rows}
    return result


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("WHO Data Fetch and Store (Async)")
    logger.info("=" * 50)
    fetched_data = fetch_and_store_who_data()
    logger.info("Final Data: %s", fetched_data)
