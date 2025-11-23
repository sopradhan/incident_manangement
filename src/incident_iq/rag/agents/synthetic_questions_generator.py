"""SyntheticQuestionsGenerator - Uses PromptModifyingAgent for meta-prompt based question generation"""
import json
import logging
from typing import List, Dict, Any
from deepagents import create_deep_agent
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QuestionGenerationInput(BaseModel):
    """Input schema for question generation"""
    document_content: str = Field(description="Document text to generate questions from")
    num_questions: int = Field(default=5, description="Number of questions to generate")
    complexity_levels: List[str] = Field(
        default=["simple", "medium", "complex"],
        description="Mix of question complexities"
    )


class SyntheticQuestionsGenerator:
    """
    Generates synthetic questions using meta-prompting via PromptModifyingAgent.
    
    Uses the same meta-prompt optimization technique as PromptModifyingAgent
    to dynamically generate diverse, quality questions from documents.
    """
    
    def __init__(self, services: dict, config: dict = None):
        """Initialize the Synthetic Questions Generator
        
        Args:
            services: Dict containing 'llm' service with get_model() method
            config: Optional configuration dict
        """
        self.services = services
        self.name = config.get('name', 'SyntheticQuestionsGenerator') if config else 'SyntheticQuestionsGenerator'
        self.llm = services.get('llm')
        
        # Meta-role system prompt for question generation specialist
        self.meta_system_prompt = (
            "You are a Question Generation Specialist. Analyze the document content and metadata. "
            "Generate ONLY valid JSON output with diverse questions at varying complexity levels. "
            "Output format: {\"questions\": [{\"question\": \"...\", \"complexity\": \"simple|medium|complex\", "
            "\"type\": \"factual|analytical|comparative|hypothetical\", \"focus\": \"...\"}], "
            "\"summary\": \"...\"}. "
            "Ensure questions test understanding, not just pattern matching."
        )
        
        # Create agent with LLM only (no external tools)
        try:
            self.agent = create_deep_agent(
                tools=[],
                system_prompt=self.meta_system_prompt,
                model=self.llm.get_model() if self.llm else None
            )
        except Exception as e:
            logger.error(f"Failed to create SyntheticQuestionsGenerator: {e}")
            raise
    
    def generate_questions(
        self,
        document_content: str,
        doc_id: str = None,
        num_questions: int = 5,
        complexity_levels: List[str] = None
    ) -> Dict[str, Any]:
        """Generate synthetic questions from document using meta-prompting
        
        Args:
            document_content: Document text to analyze
            doc_id: Document identifier for tracking
            num_questions: Number of questions to generate
            complexity_levels: List of complexity levels to mix (simple, medium, complex)
            
        Returns:
            Dict with generated questions and metadata
        """
        try:
            if complexity_levels is None:
                complexity_levels = ["simple", "medium", "complex"]
            
            # Build meta-input for question generation
            meta_input = self._build_meta_input(
                document_content,
                num_questions,
                complexity_levels,
                doc_id
            )
            
            logger.debug(f"Generating {num_questions} synthetic questions for doc: {doc_id}")
            
            # Call LLM directly using LLMService
            response = self.llm.generate_response(meta_input)
            
            # Parse JSON output
            try:
                result = json.loads(response)
                questions = result.get('questions', [])
                
                logger.info(
                    f"✓ Generated {len(questions)} synthetic questions for {doc_id} "
                    f"(complexities: {', '.join([q.get('complexity', 'unknown') for q in questions])})"
                )
                
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "num_questions": len(questions),
                    "questions": questions,
                    "summary": result.get('summary', ''),
                    "generation_method": "meta-prompting"
                }
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse question JSON: {e}")
                logger.debug(f"Response was: {response[:200]}")
                
                # Fallback: extract text questions manually
                fallback_questions = self._extract_fallback_questions(response, num_questions)
                return {
                    "success": len(fallback_questions) > 0,
                    "doc_id": doc_id,
                    "num_questions": len(fallback_questions),
                    "questions": fallback_questions,
                    "summary": "Fallback extraction from response",
                    "generation_method": "meta-prompting-fallback"
                }
                
        except Exception as e:
            logger.error(f"Error generating synthetic questions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "doc_id": doc_id,
                "num_questions": 0,
                "questions": []
            }
    
    def _build_meta_input(
        self,
        document_content: str,
        num_questions: int,
        complexity_levels: List[str],
        doc_id: str = None
    ) -> str:
        """Build structured input for the meta-agent question generation
        
        Args:
            document_content: Document text to analyze
            num_questions: Number of questions to generate
            complexity_levels: Mix of complexity levels
            doc_id: Document identifier for context
            
        Returns:
            Formatted string for meta-agent processing
        """
        # Limit document length for LLM processing
        doc_excerpt = document_content[:3000] if len(document_content) > 3000 else document_content
        
        meta_input = f"""# Document Analysis for Question Generation
Document ID: {doc_id or 'unknown'}
Document Length: {len(document_content)} chars
Excerpt (first 3000 chars):
---
{doc_excerpt}
---

# Generation Requirements
Total Questions: {num_questions}
Complexity Mix: {', '.join(complexity_levels)}

# Question Diversity Requirements
1. Question Types:
   - Factual: Direct answers from document ("What...", "When...", "Who...")
   - Analytical: Requires interpretation ("Why...", "How...", "What impact...")
   - Comparative: Multiple concepts ("Compare...", "Difference between...", "Relationship...")
   - Hypothetical: Reasoning about scenarios ("What if...", "Would...", "Could...")

2. Complexity Levels:
   - Simple: Single fact retrieval, direct from text
   - Medium: Requires combining 2-3 chunks or inference
   - Complex: Multi-hop reasoning, cross-document patterns, deep understanding

3. Coverage:
   - Questions should span different sections of document
   - Mix of specific details and general concepts
   - Vary question phrasing and structure

# Output Requirements
Generate ONLY valid JSON in this exact format:
{{
    "questions": [
        {{
            "question": "Question text here?",
            "complexity": "simple|medium|complex",
            "type": "factual|analytical|comparative|hypothetical",
            "focus": "Brief description of what this tests",
            "expected_evidence": "Where in doc to find answer"
        }}
    ],
    "summary": "Brief summary of question coverage"
}}

IMPORTANT:
- Output ONLY the JSON, no other text
- Ensure valid JSON format
- Each question must have all required fields
- Complexity and type values must be exact (no variations)
"""
        return meta_input
    
    def _extract_fallback_questions(
        self,
        response: str,
        num_questions: int
    ) -> List[Dict[str, str]]:
        """Extract questions manually when JSON parsing fails
        
        Args:
            response: LLM response text
            num_questions: Target number of questions
            
        Returns:
            List of question dicts
        """
        questions = []
        
        # Try to find Q1:, Q2:, Question 1:, etc patterns
        import re
        
        # Pattern: "Q1:", "Question 1:", "1.", etc followed by question text
        patterns = [
            r'Q\d+\s*:\s*([^?\n]+\?)',
            r'Question\s+\d+\s*:\s*([^?\n]+\?)',
            r'\d+\.\s*([^?\n]+\?)',
            r'\*\*([^?\n]+\?)\*\*',
        ]
        
        found_questions = set()
        for pattern in patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                q_text = match.strip()
                if q_text and q_text not in found_questions:
                    found_questions.add(q_text)
                    questions.append({
                        "question": q_text,
                        "complexity": "medium",  # Default when extracted via fallback
                        "type": "factual",
                        "focus": "Extracted from response",
                        "expected_evidence": "Not specified"
                    })
                    if len(questions) >= num_questions:
                        break
            
            if len(questions) >= num_questions:
                break
        
        return questions[:num_questions]
