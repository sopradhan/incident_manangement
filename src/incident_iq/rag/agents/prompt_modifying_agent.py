"""PromptModifyingAgent - Dynamic prompt orchestration and optimization"""
import json
import logging
from deepagents import create_deep_agent
from typing import Tuple

logger = logging.getLogger(__name__)


class PromptModifyingAgent:
    """Analyzes and optimizes prompts for downstream agents using meta-prompting
    
    Domain-agnostic: Works across any knowledge domain by analyzing query structure
    and available metadata, not domain-specific concepts.
    """
    
    def __init__(self, services: dict, config: dict = None):
        """Initialize the Prompt Modifying Agent
        
        Args:
            services: Dict containing 'llm' service with get_model() method
            config: Optional configuration dict
        """
        self.services = services
        self.name = config.get('name', 'PromptModifyingAgent') if config else 'PromptModifyingAgent'
        self.llm = services.get('llm')
        
        # Meta-role system prompt - domain-agnostic
        self.meta_system_prompt = (
            "You are a Query Optimization Specialist. Analyze the base system prompt, "
            "user query, and provided metadata. Your task: enhance the system prompt to be more specific "
            "and context-aware, and refine the user query to be clearer. "
            "Output ONLY an optimized system prompt and a refined query separated by '|'. "
            "Format: '<OPTIMIZED_SYSTEM_PROMPT>|<REFINED_QUERY>'. "
            "The enhanced prompt should incorporate the available metadata context. "
            "The refined query should be clearer, more focused, and more specific."
        )
        
        # Create agent with LLM only (no external tools needed)
        try:
            self.agent = create_deep_agent(
                tools=[],
                system_prompt=self.meta_system_prompt,
                model=self.llm.get_model() if self.llm else None
            )
        except Exception as e:
            logger.error(f"Failed to create PromptModifyingAgent: {e}")
            raise
    
    def generate_optimized_prompt(
        self,
        original_system_prompt: str,
        original_query: str,
        metadata: dict = None
    ) -> Tuple[str, str]:
        """Generate optimized system prompt and query using meta-prompting
        
        Domain-agnostic: Works with any type of metadata and query.
        
        Args:
            original_system_prompt: Base system prompt for downstream agent
            original_query: Original user query
            metadata: Additional context (any structure)
            
        Returns:
            Tuple of (optimized_system_prompt, refined_query)
        """
        try:
            # Build meta-input for prompt optimization
            meta_input = self._build_meta_input(
                original_system_prompt,
                original_query,
                metadata
            )
            
            # Call LLM directly using LLMService instead of agent.run()
            logger.debug(f"Optimizing prompt with metadata: {metadata}")
            combined_output = self.llm.generate_response(meta_input)
            
            # Parse output with multiple fallback strategies
            try:
                # Strategy 1: Try pipe separator
                if '|' in combined_output:
                    parts = combined_output.split('|', 1)
                    if len(parts) == 2:
                        optimized_prompt = parts[0].strip()
                        refined_query = parts[1].strip()
                        if optimized_prompt and refined_query:
                            logger.info(f"[OK] Prompt optimized ({len(optimized_prompt)} chars prompt, {len(refined_query)} chars query)")
                            return optimized_prompt, refined_query
                
                # Strategy 2: Try newline separation
                lines = [l.strip() for l in combined_output.split('\n') if l.strip()]
                if len(lines) >= 2:
                    optimized_prompt = lines[0]
                    refined_query = ' '.join(lines[1:])
                    if optimized_prompt and refined_query:
                        logger.info(f"[OK] Prompt optimized via newline parsing ({len(optimized_prompt)} chars prompt, {len(refined_query)} chars query)")
                        return optimized_prompt, refined_query
                
                # Strategy 3: Use original with metadata enhancement
                logger.warning(f"PMA output format unclear, using enhanced original. LLM output: {combined_output[:100]}...")
                enhanced_prompt = f"{original_system_prompt}\n[Context: {json.dumps(metadata) if metadata else 'N/A'}]"
                return enhanced_prompt, original_query
                
            except Exception as e:
                logger.warning(f"Failed to parse PMA output: {e}, using enhanced fallback")
                enhanced_prompt = f"{original_system_prompt}\n[Context: {json.dumps(metadata) if metadata else 'N/A'}]"
                return enhanced_prompt, original_query
                
        except Exception as e:
            logger.error(f"Error in generate_optimized_prompt: {e}", exc_info=True)
            return original_system_prompt, original_query
    
    def _build_meta_input(
        self,
        original_system_prompt: str,
        original_query: str,
        metadata: dict = None
    ) -> str:
        """Build structured input for the meta-agent (domain-agnostic)
        
        Args:
            original_system_prompt: Base system prompt
            original_query: Original query  
            metadata: Additional context (any structure, any domain)
            
        Returns:
            Formatted string for meta-agent processing
        """
        meta_input = f"""# System Prompt to Enhance
{original_system_prompt}

# User Query
{original_query}"""
        
        if metadata:
            meta_input += f"""

# Available Context Metadata
{json.dumps(metadata, indent=2)}"""
        
        meta_input += """

---
TASK: Make the system prompt more specific and context-aware using the available metadata.
Refine the user query to be clearer and more focused.

OUTPUT FORMAT (CRITICAL - Use pipe separator):
<ENHANCED_SYSTEM_PROMPT> | <REFINED_QUERY>

Example (generic, works for any domain):
You are a helpful expert who provides detailed answers based on context. Consider the provided metadata to give more targeted assistance. | What specific question do you need answered?

Now generate your enhanced prompt and refined query using the pipe separator:
"""
        return meta_input
