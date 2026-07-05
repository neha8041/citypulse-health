from app.workflows.morning_briefing import MorningBriefingWorkflow
try:
    workflow = MorningBriefingWorkflow()
    print(workflow.generate_briefing())
except Exception as e:
    import traceback
    traceback.print_exc()
