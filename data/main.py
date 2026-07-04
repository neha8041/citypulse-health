import functions_framework
from data_loader import run

@functions_framework.http
def scheduled_data_load(request):
    """HTTP Cloud Function triggered by Cloud Scheduler every night"""
    try:
        run()
        return {"status": "success", "message": "Data load completed"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
