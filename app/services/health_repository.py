import asyncio
from typing import Dict, Any
from google.cloud import bigquery

from app.core.config import PROJECT_ID, DATASET_ID, logger

class HealthRepository:
    """Data Access Layer for fetching health signals and metrics from BigQuery."""

    def __init__(self) -> None:
        logger.info("Initializing HealthRepository")
        self.bq_client = bigquery.Client(project=PROJECT_ID)

    async def get_zone_health_status(self, zone_id: str) -> Dict[str, Any]:
        """Get the latest health status for a specific zone."""
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
            WHERE d.zone_id = @zone_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("zone_id", "STRING", zone_id)
            ]
        )

        def run_query():
            logger.info(f"Executing get_zone_health_status for {zone_id}")
            return list(self.bq_client.query(query, job_config=job_config).result())

        results = await asyncio.to_thread(run_query)
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

    async def get_all_zones_summary(self) -> Dict[str, Any]:
        """Get a summary of all zones ranked by risk level."""
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
        def run_query():
            return list(self.bq_client.query(query).result())
            
        results = await asyncio.to_thread(run_query)
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

    async def get_anomalies(self) -> Dict[str, Any]:
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
        def run_query():
            return list(self.bq_client.query(query).result())
            
        results = await asyncio.to_thread(run_query)
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

    async def get_city_summary(self) -> Dict[str, Any]:
        """Get the overall city health summary for today."""
        query = f"""
            SELECT *
            FROM `{PROJECT_ID}.{DATASET_ID}.city_summary`
            ORDER BY recorded_at DESC
            LIMIT 1
        """
        def run_query():
            return list(self.bq_client.query(query).result())
            
        results = await asyncio.to_thread(run_query)
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
