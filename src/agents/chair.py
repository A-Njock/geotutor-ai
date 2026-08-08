from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import get_llm

class ChairAgent:
    def __init__(self):
        # The Chair also operates on DeepSeek for testing
        self.llm = get_llm("deepseek")

    def decide_next_speaker(self, state: dict) -> str:
        """
        Decides who should speak next based on the conversation history.
        Returns: 'librarian', 'analyst', 'engineer', 'critic', or 'FINISH'.
        """
        messages = state.get("messages", [])
        # Extract last few messages to understand context
        # In a real app, we'd pass structured history
        history_summary = "\n".join([f"{m.type}: {m.content[:200]}..." for m in messages[-5:]])
        
        template = """You are the Chair of the Geotechnical Council. 
        Your goal is to ensure a rigorous solution to the user's problem by orchestrating the debate.
        
        Council Members:
        1. Librarian: Finds information/context.
        2. Analyst: Plans the solution.
        3. Engineer: Calculates.
        4. Critic: Reviews.
        
        Current State:
        {history}
        
        Plan: {plan}
        Code: {code}
        Result: {result}
        Critique: {critique}

        Rules:
        - Start with Librarian if context is missing.
        - Then Analyst to plan.
        - Then Engineer to execute.
        - Then Critic to review.
        - If Critic REJECTS, go back to Analyst or Engineer.
        - If Critic APPROVES, you (Chair) make the final statement and end with 'FINISH'.
        
        Output one word ONLY: 'librarian', 'analyst', 'engineer', 'critic', or 'FINISH'.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        # Using a specialized runnable that just calling invoke
        chain = prompt | self.llm | StrOutputParser()
        
        # Access state variables safely
        plan = state.get("plan", "None")
        code = state.get("code", "None")
        result = state.get("result", "None")
        critique = state.get("critique", "None")
        
        decision = chain.invoke({
            "history": history_summary,
            "plan": plan, 
            "code": code, 
            "result": result, 
            "critique": critique
        })
        
        decision = decision.strip().lower()
        print(f"--- CHAIR DECISION: {decision.upper()} ---")
        return decision

if __name__ == "__main__":
    chair = ChairAgent()
    # Mock state
    # print(chair.decide_next_speaker({"messages": []}))
