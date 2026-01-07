from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ..agents.utils import get_llm
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
import time
import json
import re

class Visualizer:
    def __init__(self):
        self.llm = get_llm("deepseek")  # Efficient for code generation
        self.output_dir = "outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_mindmap_data(self, topic: str, context: str) -> dict:
        """
        Generates structured JSON data for a mindmap from the LLM.
        """
        template = """You are a visualization expert for geotechnical engineering concepts.
        Create a hierarchical mindmap structure for the topic: '{topic}'.
        Use the provided context to ensure technical accuracy.
        
        Context:
        {context}
        
        Output STRICTLY valid JSON in this exact format (no markdown, no explanation):
        {{
            "root": "Main Topic Name",
            "branches": [
                {{
                    "name": "Branch 1",
                    "children": ["Leaf 1a", "Leaf 1b", "Leaf 1c"]
                }},
                {{
                    "name": "Branch 2", 
                    "children": ["Leaf 2a", "Leaf 2b"]
                }}
            ]
        }}
        
        Guidelines:
        - Keep branch names short (2-4 words)
        - Use 3-6 main branches
        - Each branch should have 2-5 children
        - Focus on the key concepts from the context
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        raw_output = chain.invoke({"topic": topic, "context": context})
        
        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', raw_output)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"[WARN] JSON parsing failed: {e}")
            # Return a fallback structure
            return {
                "root": topic,
                "branches": [
                    {"name": "Key Concepts", "children": ["See text response"]},
                    {"name": "Applications", "children": ["Refer to answer"]}
                ]
            }

    def render_matplotlib_mindmap(self, data: dict) -> str:
        """
        Render a mindmap using matplotlib and return the path to the saved PNG.
        Creates a radial/tree layout visualization.
        """
        fig, ax = plt.subplots(1, 1, figsize=(14, 10), facecolor='#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        ax.set_xlim(-10, 10)
        ax.set_ylim(-8, 8)
        ax.axis('off')
        
        root_name = data.get("root", "Topic")
        branches = data.get("branches", [])
        
        # Colors for branches (gradient palette)
        branch_colors = ['#e94560', '#0f3460', '#16213e', '#533483', '#e76f51', '#2a9d8f']
        
        # Draw root node (center)
        root_circle = plt.Circle((0, 0), 1.5, color='#e94560', ec='white', linewidth=3, zorder=10)
        ax.add_patch(root_circle)
        ax.text(0, 0, root_name, ha='center', va='center', fontsize=12, 
                fontweight='bold', color='white', wrap=True, zorder=11)
        
        # Calculate branch positions (radial layout)
        n_branches = len(branches)
        if n_branches == 0:
            n_branches = 1
        
        angles = np.linspace(0, 2 * np.pi, n_branches, endpoint=False)
        branch_radius = 4.5
        
        for i, (branch, angle) in enumerate(zip(branches, angles)):
            branch_name = branch.get("name", f"Branch {i+1}")
            children = branch.get("children", [])
            color = branch_colors[i % len(branch_colors)]
            
            # Branch position
            bx = branch_radius * np.cos(angle)
            by = branch_radius * np.sin(angle)
            
            # Draw line from root to branch
            ax.plot([0, bx], [0, by], color=color, linewidth=2.5, zorder=1)
            
            # Draw branch node
            branch_circle = plt.Circle((bx, by), 0.9, color=color, ec='white', linewidth=2, zorder=5)
            ax.add_patch(branch_circle)
            ax.text(bx, by, branch_name, ha='center', va='center', fontsize=9, 
                    fontweight='bold', color='white', wrap=True, zorder=6)
            
            # Draw children (leaves)
            n_children = len(children)
            if n_children > 0:
                # Spread children in a fan around the branch
                child_spread = min(np.pi / 3, np.pi / (n_children + 1))
                child_angles = np.linspace(angle - child_spread, angle + child_spread, n_children)
                child_radius = 2.5
                
                for j, (child, child_angle) in enumerate(zip(children, child_angles)):
                    cx = bx + child_radius * np.cos(child_angle)
                    cy = by + child_radius * np.sin(child_angle)
                    
                    # Draw line from branch to child
                    ax.plot([bx, cx], [by, cy], color=color, linewidth=1.5, alpha=0.7, zorder=1)
                    
                    # Draw leaf node (smaller)
                    leaf_circle = plt.Circle((cx, cy), 0.5, color=color, alpha=0.6, 
                                             ec='white', linewidth=1, zorder=3)
                    ax.add_patch(leaf_circle)
                    
                    # Truncate long text
                    display_text = child[:20] + "..." if len(child) > 20 else child
                    ax.text(cx, cy, display_text, ha='center', va='center', fontsize=7, 
                            color='white', wrap=True, zorder=4)
        
        # Add title
        ax.text(0, 7.5, f"Mind Map: {root_name}", ha='center', va='center', fontsize=14, 
                fontweight='bold', color='white')
        
        plt.tight_layout()
        
        # Save figure
        timestamp = int(time.time())
        filepath = os.path.join(self.output_dir, f"mindmap_{timestamp}.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a2e', edgecolor='none')
        plt.close(fig)
        
        return os.path.abspath(filepath)

    def generate_mindmap(self, topic: str, context: str) -> str:
        """
        Full pipeline: Generate mindmap data and render to image.
        Returns the path to the generated PNG file.
        """
        data = self.generate_mindmap_data(topic, context)
        image_path = self.render_matplotlib_mindmap(data)
        return image_path


if __name__ == "__main__":
    v = Visualizer()
    test_data = {
        "root": "Bearing Capacity",
        "branches": [
            {"name": "Terzaghi", "children": ["Nc", "Nq", "Nγ", "Shape Factors"]},
            {"name": "Meyerhof", "children": ["Depth Factors", "Inclined Load"]},
            {"name": "Vesic", "children": ["General Shear", "Local Shear"]},
            {"name": "Factors", "children": ["Cohesion", "Surcharge", "Unit Weight"]}
        ]
    }
    path = v.render_matplotlib_mindmap(test_data)
    print(f"Test mindmap saved to: {path}")
