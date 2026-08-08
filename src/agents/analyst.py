from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import get_llm

class AnalystAgent:
    def __init__(self):
        self.llm = get_llm("gpt-4o")

    def analyze(self, query: str, context: str):
        """
        Formulates a step-by-step plan to solve the geotechnical problem.
        """
        template = """You are The Analyst, a senior geotechnical engineer.
        Your goal is to break down a complex user query into a calculation plan.
        
        Context from Librarian:
        {context}

        User Query: {query}

        Instructions:
        1. Identify the key geotechnical parameters needed.
        2. Select the appropriate theoretical method (e.g., Terzaghi, Vesic, Eurocode 7).
        3. Create a numbered list of steps for the Engineer to calculate.
        4. Do NOT perform the calculation yourself. Just describe the formula/logic.
        
        Output:
        A concise, numbered implementation plan.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"query": query, "context": context})

if __name__ == "__main__":
    analyst = AnalystAgent()
    # Test
    # print(analyst.analyze("Design a square footing...", "Context..."))
