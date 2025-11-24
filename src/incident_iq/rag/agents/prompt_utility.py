import json
import logging

logger = logging.getLogger(__name__)


class PromptUtility:
    def __init__(self, llm_service):
        self.llm = llm_service
        self.name = "PromptUtility"
    
    def refine_query(self, original_query: str, context: str = None) -> str:
        try:
            meta_input = f"""# Query Refinement Task
Original Query: {original_query}"""
            
            if context:
                meta_input += f"\n\nAvailable Context:\n{context}"
            
            meta_input += """

---
TASK: Refine this query to be clearer, more focused, and more specific.
The refined query should:
1. Clarify ambiguities
2. Add specificity where needed
3. Improve semantic searchability
4. Maintain the original intent

OUTPUT FORMAT: Just provide the refined query, no explanation needed.
Refined Query:"""
            
            response = self.llm.generate_response(meta_input).strip()
            
            if response and response.lower() != original_query.lower():
                logger.debug(f"Query refined: '{original_query[:50]}...' → '{response[:50]}...'")
                return response
            
            return original_query
            
        except Exception as e:
            logger.warning(f"Query refinement failed: {e}, returning original")
            return original_query
    
    def optimize_system_prompt(self, base_prompt: str, query: str = None, 
                               metadata: dict = None) -> str:
        try:
            meta_input = f"""# System Prompt Optimization Task
Base System Prompt:
{base_prompt}"""
            
            if query:
                meta_input += f"\n\nUser Query Context:\n{query}"
            
            if metadata:
                meta_input += f"\n\nAvailable Metadata:\n{json.dumps(metadata, indent=2)}"
            
            meta_input += """

---
TASK: Enhance this system prompt to be more specific and context-aware.
The enhanced prompt should:
1. Incorporate the provided context
2. Be more specific and targeted
3. Improve decision-making for the LLM
4. Maintain the original core intent

OUTPUT FORMAT: Just provide the enhanced prompt, no explanation needed.
Enhanced System Prompt:"""
            
            response = self.llm.generate_response(meta_input).strip()
            
            if response and response.lower() != base_prompt.lower():
                logger.debug(f"System prompt optimized ({len(base_prompt)} → {len(response)} chars)")
                return response
            
            return base_prompt
            
        except Exception as e:
            logger.warning(f"Prompt optimization failed: {e}, returning original")
            return base_prompt
    
    def clarify_intent(self, query: str) -> dict:
        try:
            meta_input = f"""# Query Intent Analysis
Query: {query}

---
TASK: Analyze this query to understand user intent.
Provide a JSON response with:
- intent: What is the user trying to accomplish?
- query_type: factual|analytical|comparative|hypothetical
- keywords: List of key topics/concepts
- complexity: simple|medium|complex (based on structure, not just content)
- requires_context: true|false (does it need external context?)

OUTPUT FORMAT: Return ONLY valid JSON, no other text.
{{
    "intent": "...",
    "query_type": "...",
    "keywords": [...],
    "complexity": "...",
    "requires_context": true|false
}}
"""
            
            response = self.llm.generate_response(meta_input)
            
            try:
                result = json.loads(response)
                logger.debug(f"Intent analysis: type={result.get('query_type')}, complexity={result.get('complexity')}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse intent analysis JSON: {response[:100]}")
                return {
                    "intent": "unknown",
                    "query_type": "factual",
                    "keywords": [],
                    "complexity": "medium",
                    "requires_context": True
                }
                
        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}")
            return {
                "intent": "unknown",
                "query_type": "factual",
                "keywords": [],
                "complexity": "medium",
                "requires_context": True
            }
    
    def generate_search_variants(self, query: str, num_variants: int = 3) -> list:
        try:
            meta_input = f"""# Query Variant Generation
Original Query: {query}

---
TASK: Generate {num_variants} alternative ways to express this query.
Each variant should:
1. Maintain the original intent
2. Use different wording/structure
3. Potentially match different documents
4. Be valid search queries

OUTPUT FORMAT: Return ONLY a JSON array of strings (one query per element).
["variant 1", "variant 2", "variant 3", ...]
"""
            
            response = self.llm.generate_response(meta_input)
            
            try:
                variants = json.loads(response)
                if isinstance(variants, list):
                    variants = [str(v) for v in variants[:num_variants]]
                    logger.debug(f"Generated {len(variants)} query variants")
                    return variants
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse query variants JSON")
            
            return [query]  # Fallback
                
        except Exception as e:
            logger.warning(f"Query variant generation failed: {e}")
            return [query]
