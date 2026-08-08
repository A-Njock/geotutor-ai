from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import get_llm
from ..tools.calculator import GeotechCalculator

class EngineerAgent:
    def __init__(self):
        self.llm = get_llm("gpt-4o")
        self.calculator = GeotechCalculator()

    def solve(self, problem_description: str, plan: str):
        """
        Generates Python code to solve the problem based on the Analyst's plan.
        """
        template = """You are The Engineer, a geotechnical computational agent.
        Your goal is to write Python code to solve a specific problem.
        
        Input:
        Problem: {problem}
        Plan: {plan}

        Instructions:
        1. Write strictly valid Python code.
        2. Define all variables clearly.
        3. Store the final answer in a variable named 'result'.
        4. Do NOT use external libraries other than math and numpy (as np).
        5. Output ONLY the code, no markdown backticks.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        code = chain.invoke({"problem": problem_description, "plan": plan})
        
        # Clean code (remove markdown if LLM adds it despite instructions)
        code = code.replace("```python", "").replace("```", "").strip()
        
        print(f"--- Generated Code ---\n{code}\n----------------------")
        
        # Execute
        execution_result = self.calculator.execute(code)
        return execution_result, code

if __name__ == "__main__":
    eng = EngineerAgent()
    # Mock test
    res = eng.calculator.execute("result = 2+2")
    print(res)
