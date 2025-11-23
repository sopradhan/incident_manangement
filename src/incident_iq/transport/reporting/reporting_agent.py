
from datetime import datetime
from ..transport_models import Incident, IncidentReport
import json

class ReportingAgent:
    """Generate incident reports using LangChain ChatOpenAI"""

    def __init__(self):
        pass

    def generate_report(self, incident: Incident) -> IncidentReport:
        return IncidentReport(
            incident_id="123",
            summary="summary",
            generated_at=datetime.now().isoformat(),
            root_cause="root cause",
            recommendations=["text1"]
        )
