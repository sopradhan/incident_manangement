import asyncio
import json
from incident_iq.transport.transport_models import IncidentContext
from .orchestrator import IncidentManagementSystem

class Transporter:
    def __init__(self):
        self.ims = IncidentManagementSystem()

    async def process(self, classifier_item):
        if isinstance(classifier_item, str):
            classifier_item = json.loads(classifier_item)

        payload = classifier_item.get("payload")
        if isinstance(payload, str):
            classifier_item["payload"] = json.loads(payload)

        try:
            context = IncidentContext(
                business_hours=classifier_item.get("business_hours", True),
                weekend=classifier_item.get("weekend", False),
                peak_traffic_hours=classifier_item.get("peak_traffic_hours", False),
                customer_facing=classifier_item.get("customer_facing", True),
                revenue_impacting=classifier_item.get("revenue_impacting", False)
            )

            await self.ims.process_incident(classifier_item, context)

        except Exception as e:
            print(f"❌ Error processing queue item: {e}\n")
            await asyncio.sleep(0.5)
