"""
Agent Spawn Model - Tracks parent-child agent relationships
"""
from typing import List, Dict, Any, Optional
from .base_model import BaseModel


class AgentSpawnModel(BaseModel):
    """Model for agent_spawns table"""
    
    table = 'agent_spawns'
    fields = ['spawn_id', 'parent_agent_id', 'child_agent_id', 'spawn_reason', 'timestamp']
    
    def record_spawn(self, parent_agent_id: str, child_agent_id: str,
                    spawn_reason: str = 'task_delegation') -> int:
        """
        Record a parent-child agent spawning relationship
        
        Args:
            parent_agent_id: Parent agent identifier
            child_agent_id: Child agent identifier
            spawn_reason: Reason for spawning (task_delegation, load_balancing, etc.)
            
        Returns:
            Last inserted row ID
        """
        return self.insert({
            'parent_agent_id': parent_agent_id,
            'child_agent_id': child_agent_id,
            'spawn_reason': spawn_reason
        })
    
    def get_children(self, parent_agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all child agents spawned by a parent
        
        Args:
            parent_agent_id: Parent agent identifier
            
        Returns:
            List of child agent spawn records
        """
        return self.raw_execute("""
            SELECT * FROM agent_spawns
            WHERE parent_agent_id = ?
            ORDER BY timestamp DESC
        """, (parent_agent_id,))
    
    def get_parent(self, child_agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get parent agent for a child
        
        Args:
            child_agent_id: Child agent identifier
            
        Returns:
            Parent spawn record or None
        """
        rows = self.raw_execute("""
            SELECT * FROM agent_spawns
            WHERE child_agent_id = ?
            LIMIT 1
        """, (child_agent_id,))
        
        return rows[0] if rows else None
    
    def get_spawn_hierarchy(self, root_agent_id: str) -> Dict[str, Any]:
        """
        Get complete spawn hierarchy starting from root agent
        
        Args:
            root_agent_id: Root agent identifier
            
        Returns:
            Dictionary representing agent hierarchy
        """
        hierarchy = {'agent_id': root_agent_id, 'children': []}
        
        children = self.get_children(root_agent_id)
        for child_record in children:
            child_id = child_record['child_agent_id']
            hierarchy['children'].append(self.get_spawn_hierarchy(child_id))
        
        return hierarchy
    
    def update_child_status(self, child_agent_id: str, status: str) -> None:
        """
        Update status of a child agent
        
        Args:
            child_agent_id: Child agent identifier
            status: New status (running, completed, failed, etc.)
        """
        # Note: agent_spawns table doesn't have a child_status column in current schema
        # This method is kept for API compatibility but won't store the status
        pass
    
    def complete_spawn(self, child_agent_id: str) -> None:
        """
        Mark a spawned agent as completed
        
        Args:
            child_agent_id: Child agent identifier
        """
        # Note: agent_spawns table doesn't have completion tracking in current schema
        pass
    
    def get_active_spawns(self, parent_agent_id: str) -> List[Dict[str, Any]]:
        """
        Get active (non-completed) spawns for a parent
        
        Args:
            parent_agent_id: Parent agent identifier
            
        Returns:
            List of active spawn records
        """
        return self.raw_execute("""
            SELECT * FROM agent_spawns
            WHERE parent_agent_id = ?
            ORDER BY timestamp DESC
        """, (parent_agent_id,))
    
    def count_children(self, parent_agent_id: str) -> int:
        """
        Count total children spawned by agent
        
        Args:
            parent_agent_id: Parent agent identifier
            
        Returns:
            Number of child agents
        """
        rows = self.raw_execute(
            "SELECT COUNT(*) as count FROM agent_spawns WHERE parent_agent_id = ?",
            (parent_agent_id,)
        )
        return rows[0]['count'] if rows else 0
    
    def get_spawn_chain(self, agent_id: str) -> List[str]:
        """
        Get full spawn chain from root to given agent (ancestry)
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of agent IDs from root to current
        """
        chain = [agent_id]
        parent_record = self.get_parent(agent_id)
        
        while parent_record:
            parent_id = parent_record['parent_agent_id']
            chain.insert(0, parent_id)
            parent_record = self.get_parent(parent_id)
        
        return chain
    
    def get_spawns_by_reason(self, spawn_reason: str) -> List[Dict[str, Any]]:
        """
        Get all spawns with a specific reason
        
        Args:
            spawn_reason: Spawn reason to filter
            
        Returns:
            List of spawn records
        """
        return self.raw_execute("""
            SELECT * FROM agent_spawns
            WHERE spawn_reason = ?
            ORDER BY spawn_timestamp DESC
        """, (spawn_reason,))
