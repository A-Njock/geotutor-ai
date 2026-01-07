from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import get_llm

class CriticAgent:
    def __init__(self):
        self.llm = get_llm("gpt-4o")

    def review(self, query: str, plan: str, code: str, result: str):
        """
        Reviews the entire process for errors, unit consistency, and compliance.
        """
        template = """You are The Critic, a geotechnical code compliance officer.
        Review the following solution package.

        User Query: {query}
        Analyst Plan: {plan}
        Engineer Code: 
        {code}
        Result: {result}

        Instructions:
        1. Check if the result makes physical sense (e.g., Bearing capacity > 0).
        2. Check for unit consistency (kPa vs Pa, m vs mm).
        3. Verify if typical factors of safety were considered (if applicable).
        
        Output:
        If PASS: "APPROVED. [Summary of result]"
        If FAIL: "REJECTED. [Reason]"
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"query": query, "plan": plan, "code": code, "result": result})
