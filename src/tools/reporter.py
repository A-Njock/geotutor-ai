import os

class ReportGenerator:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, title: str, sections: dict):
        """
        Generates a markdown report from the council's findings.
        """
        content = f"# {title}\n\n"
        
        if "Query" in sections:
            content += f"## Problem Statement\n{sections['Query']}\n\n"
            
        if "Plan" in sections:
            content += f"## Analysis Approach\n{sections['Plan']}\n\n"
            
        if "Code" in sections:
            content += f"## Calculation Code\n```python\n{sections['Code']}\n```\n\n"
            
        if "Result" in sections:
            content += f"## Results\n{sections['Result']}\n\n"
            
        if "Critique" in sections:
            content += f"## Compliance Review\n{sections['Critique']}\n\n"
            
        filename = f"{title.replace(' ', '_').lower()}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return filepath

if __name__ == "__main__":
    rep = ReportGenerator()
    path = rep.generate_report("Test Report", {"Query": "Demo", "Result": "42"})
    print(f"Report saved to {path}")
