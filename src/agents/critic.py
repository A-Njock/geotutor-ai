from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import get_llm

class CriticAgent:
    def __init__(self):
        self.llm = get_llm("gpt-4o")

    def review(self, query: str, plan: str, code: str, result: str):
        """
        Reviews the entire process for quality, accuracy, and educational value.
        Adapts review criteria based on question type (educational vs engineering calculation).
        """
        template = """You are The Critic, a geotechnical engineering education quality reviewer.
        Review the following answer for accuracy and educational value.

        User Query: {query}
        Analyst Plan: {plan}
        Result: {result}

        Instructions:
        First, determine the type of question:
        - EDUCATIONAL: concept explanations, definitions, theory, history, standards, procedures
        - CALCULATION: numerical problems, design calculations, bearing capacity, settlement, etc.

        For EDUCATIONAL questions:
        1. Check if the answer is accurate and relevant to geotechnical engineering
        2. Verify the explanation is clear and educational
        3. Confirm key concepts are correctly explained
        
        For CALCULATION questions:
        1. Check if the result makes physical sense (e.g., Bearing capacity > 0)
        2. Check for unit consistency (kPa vs Pa, m vs mm)
        3. Verify if typical factors of safety were considered (if applicable)
        
        Output format:
        - If the answer is accurate and helpful: "APPROVED. [Brief quality summary, max 1-2 sentences]"
        - If there are significant errors or issues: "NEEDS IMPROVEMENT. [Specific issue to address]"
        
        Be constructive and fair. Most educational explanations should be approved if they are accurate.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"query": query, "plan": plan, "code": code, "result": result})

