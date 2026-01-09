"""
NanoBanana Visual Generator - Pedagogical Image Generation
Uses Google Gemini 2.5 Flash Image model to create educational visuals
"""
import os
import base64
from typing import Optional, Literal
from pathlib import Path
import google.generativeai as genai
from datetime import datetime

# Visual types supported
VisualType = Literal["flowchart", "diagram", "infographic", "illustration"]


class VisualGenerator:
    """
    Generates pedagogical visuals using Google Gemini 2.5 Flash Image model.
    Takes visual type and LLM response to create educational diagrams.
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.output_dir = Path("outputs/visuals")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _build_prompt(self, visual_type: VisualType, llm_response: str, topic_summary: str = "") -> str:
        """
        Build an adaptive, high-quality prompt for pedagogical visual generation.
        The prompt is flexible but maintains rigorous educational standards.
        """
        # Extract topic summary from response if not provided
        if not topic_summary:
            # Use first sentence or first 50 chars as topic
            topic_summary = llm_response.split('.')[0][:100] if llm_response else "Geotechnical Concept"
        
        # Visual-type specific guidance
        visual_guidance = {
            "flowchart": """
                Create an intuitive process flow visualization:
                - Use clean, connected blocks showing sequential steps
                - Include decision points with diamond shapes where applicable
                - Show soil/stress transitions with gradient arrows
                - Highlight critical paths and failure modes
                - Use isometric 3D blocks for soil layers when relevant""",
            
            "diagram": """
                Create an explanatory technical diagram:
                - Use exploded cross-sections to show internal relationships
                - Include force vectors with magnitude labels
                - Show Mohr circles for stress analysis if applicable
                - Add dimensional annotations and scale references
                - Layer information from surface to detailed""",
            
            "infographic": """
                Create a data-rich infographic visualization:
                - Use vertical timeline or comparison layouts
                - Include statistical charts (bar, line, pie) where data exists
                - Show safety factor ranges with color gradients
                - Present before/after or stable/failure comparisons
                - Make numbers and percentages prominent""",
            
            "illustration": """
                Create a conceptual illustration:
                - Use real-world analogies to explain abstract concepts
                - Include human-scale references (engineer, equipment)
                - Show cause-and-effect relationships visually
                - Make the concept memorable through visual metaphor
                - Balance technical accuracy with accessibility"""
        }
        
        prompt = f"""Generate a MASTERPIECE pedagogical illustration that visually explains the following geotechnical engineering content.

## YOUR TASK
Create a {visual_type.upper()} visualization for:
TOPIC: {topic_summary}

CONTENT TO VISUALIZE (use ONLY this - no inventions):
{llm_response[:2000]}

## VISUAL TYPE GUIDANCE
{visual_guidance.get(visual_type, visual_guidance["diagram"])}

## QUALITY STANDARDS (Publication-Ready)
- Crystal-clear, high-resolution output suitable for textbooks
- Clean white or light gray background for maximum readability
- Professional color palette: Blues (#4A90E2) for primary elements, 
  Orange (#FF6B35) for warnings/highlights, Grays for structure
- Typography: Clear sans-serif fonts, hierarchical sizing
- Precise annotations with numbered callouts and leader lines

## MANDATORY PEDAGOGICAL ELEMENTS
1. CLEAR TITLE at top describing the concept
2. NUMBERED ANNOTATIONS (1, 2, 3...) pointing to key features
3. LEGEND/KEY explaining symbols and colors used
4. SCALE REFERENCE where applicable (human figure, dimensions)
5. KEY EQUATIONS or VALUES prominently displayed if mentioned in content
6. FLOW ARROWS showing processes, forces, or relationships
7. COMPARISON elements (before/after, good/bad) if applicable

## GEOTECHNICAL SPECIFICS
- Use standard soil mechanics symbols (USCS notation)
- Include Mohr circles for stress analysis content
- Show force vectors with proper arrow conventions
- Display safety factors prominently when mentioned
- Use realistic soil textures (sandy, clayey, gravel) appropriately

## COGNITIVE DESIGN PRINCIPLES
- Maximum 7±2 main elements for cognitive load management
- F-pattern or Z-pattern scan path for reading flow
- Progressive disclosure: core concept center, details radiate outward
- Dual coding: every term has both text AND visual representation
- Concrete examples over abstract representations

## STRICT FIDELITY RULES
- Extract concepts, equations, values EXACTLY from the provided content
- If content mentions specific parameters (φ=30°, FS=1.5), show them
- Do NOT add generic examples or fabricate data
- If something is unclear in the content, simplify rather than invent

## OUTPUT REQUIREMENTS
- Single cohesive composition (square 1:1 aspect ratio preferred)
- Self-explanatory: should make sense without additional text
- Print-ready quality with sharp edges and no artifacts
- Geotechnical engineering textbook aesthetic

Create an educational visual that would impress both students learning the concept 
and professors evaluating teaching materials. Make it information-dense but visually 
elegant - every pixel should serve a pedagogical purpose."""
        
        return prompt
    
    def generate(
        self, 
        visual_type: VisualType, 
        llm_response: str,
        topic_summary: str = "",
        save: bool = True
    ) -> dict:
        """
        Generate a pedagogical visual based on the visual type and LLM response.
        
        Args:
            visual_type: Type of visual (flowchart, diagram, infographic, illustration)
            llm_response: The LLM-generated answer to visualize
            topic_summary: Optional short summary of the topic
            save: Whether to save the image to disk
            
        Returns:
            dict with 'success', 'image_path', 'image_base64', 'error'
        """
        try:
            prompt = self._build_prompt(visual_type, llm_response, topic_summary)
            
            # Generate image using Gemini
            response = self.model.generate_content(prompt)
            
            # Extract image data
            if response.parts and hasattr(response.parts[0], 'inline_data'):
                image_data = response.parts[0].inline_data.data
                mime_type = response.parts[0].inline_data.mime_type
                
                # Determine file extension
                ext = "png" if "png" in mime_type else "jpg"
                
                # Save if requested
                image_path = None
                if save:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{visual_type}_{timestamp}.{ext}"
                    image_path = self.output_dir / filename
                    
                    # Decode and save
                    with open(image_path, "wb") as f:
                        f.write(base64.b64decode(image_data))
                
                return {
                    "success": True,
                    "image_path": str(image_path) if image_path else None,
                    "image_base64": image_data,
                    "mime_type": mime_type,
                    "error": None
                }
            else:
                # If no image in response, might be text-only
                return {
                    "success": False,
                    "image_path": None,
                    "image_base64": None,
                    "error": "No image generated - model returned text only"
                }
                
        except Exception as e:
            return {
                "success": False,
                "image_path": None,
                "image_base64": None,
                "error": str(e)
            }
    
    def generate_from_context(
        self,
        question: str,
        answer: str,
        visual_type: VisualType = "diagram"
    ) -> dict:
        """
        Convenience method that extracts topic from question and generates visual.
        
        Args:
            question: The original user question
            answer: The LLM-generated answer
            visual_type: Type of visual to generate
            
        Returns:
            dict with generation results
        """
        # Use question as topic summary
        topic = question[:100] if len(question) > 100 else question
        return self.generate(visual_type, answer, topic)


# Singleton instance for easy import
_generator = None

def get_visual_generator() -> VisualGenerator:
    """Get or create the visual generator singleton."""
    global _generator
    if _generator is None:
        _generator = VisualGenerator()
    return _generator


if __name__ == "__main__":
    # Test the generator
    generator = VisualGenerator()
    
    test_response = """
    Soil consolidation is the process by which soil decreases in volume over time 
    when subjected to an increase in load. The key equation is:
    
    Settlement = Cc * H * log((σ'0 + Δσ) / σ'0) / (1 + e0)
    
    Where:
    - Cc = compression index
    - H = layer thickness
    - σ'0 = initial effective stress
    - Δσ = stress increase
    - e0 = initial void ratio
    
    The process occurs in three phases:
    1. Initial compression (immediate)
    2. Primary consolidation (weeks to months)
    3. Secondary compression (creep, years)
    """
    
    result = generator.generate(
        visual_type="diagram",
        llm_response=test_response,
        topic_summary="Soil Consolidation Process"
    )
    
    print(f"Generation result: {result}")
