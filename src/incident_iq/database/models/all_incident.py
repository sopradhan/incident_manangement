from .base_model import BaseModel

class AllIncidentModel(BaseModel):
    table = 'all_incidents'
    fields = ['id','source','title','description','priority','urgency','status','created_at','last_updated','reporter','assigned_to','pd_incident_id','pd_service_id','pd_escalation_policy','pd_html_url','jira_ticket_id','jira_project','jira_issue_type','jira_url','slack_channel','slack_thread_ts','slack_user','slack_permalink']