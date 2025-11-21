from .base_model import BaseModel


class KnowledgeBaseModel(BaseModel):
    table = 'knowledge_base'
    fields = ['id', 'cause', 'description', 'impact','remediation_steps','rca','business_impact','estimated_recovery_time','dollar_impact','resource_type','environment','created_at']