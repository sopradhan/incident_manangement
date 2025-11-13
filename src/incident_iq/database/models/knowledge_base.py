from .base_model import BaseModel


class KnowledgeBaseModel(BaseModel):
    table = 'knowledge_base'
    fields = ['id', 'cause', 'description', 'impact','remediation_steps','rca','business_impact','estimated_recovery_time','environment','created_at']
