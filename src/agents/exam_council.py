import re
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import call_llm, KEYS

# Reusing the same Council Members
COUNCIL_MEMBERS = [
    {"name": "Member_DeepSeek", "family": "deepseek", "model": "deepseek-chat", "key": KEYS["deepseek"]},
    {"name": "Member_GPT", "family": "gpt", "model": "gpt-4o", "key": KEYS["gpt"]},
    {"name": "Member_Mistral", "family": "mistral", "model": "mistral-large-latest", "key": KEYS["mistral"]}
]

class ExamCouncil:
    def __init__(self):
        pass

    def design_exams(self, query: str, context: str) -> str:
        """
        Orchestrates the exam creation process:
        1. Proposal (Plan structure)
        2. Drafting (Write questions)
        3. Review (Consensus check)
        """
        print("--- [EXAM COUNCIL] Session Started ---")
        
        # Step 1: Proposal Phase (Parallel)
        prompt_design = f"""You are a member of the Geotechnical Exam Board.
        User Request: {query}
        
        Context (Previous Exams/Codes):
        {context}
        
        Task:
        Propose a high-level EXAM STRUCTURE (Outline only).
        - Targeted difficulty level.
        - Number of questions.
        - Topics per question (Theory vs Calculation vs Design).
        - Justify choice based on context.
        """
        
        proposals = self._parallel_consult(prompt_design)
        # For simplicity, we synthesize the best proposal immediately using DeepSeek as Chair
        synthesis_prompt = f"""You are the Exam Chair. Synthesize a SINGLE Exam Structure based on these proposals:\n{proposals}\n\nOutput the consolidated Plan."""
        exam_plan = call_llm(synthesis_prompt, "deepseek", "deepseek-chat", KEYS["deepseek"])
        print(f"--- [EXAM COUNCIL] Plan Agreed ---\n{exam_plan[:200]}...")
        
        # Step 2: Drafting Phase
        prompt_draft = f"""You are the Exam Author.
        Draft the FULL EXAM CONTENT based on this Plan:
        {exam_plan}
        
        Use the Context to ensure questions are realistic and technically accurate.
        Reference specific codes (Eurocode/ASTM) where applicable.
        
        Format:
        **Question 1** (X points): [Text]
        **Question 2** (X points): [Text]
        ...
        """
        # We can accept one draft or multiple. Let's get one high quality draft from GPT or DeepSeek
        draft = call_llm(prompt_draft, "gpt", "gpt-4o", KEYS["gpt"])
        
        # Step 3: Review/Critique
        prompt_review = f"""You are the External Examiner.
        Review this Draft Exam:
        {draft}
        
        Check for:
        - Clarity
        - Fairness/Difficulty balance
        - Alignment with the Plan
        
        If good, output 'APPROVED'. If not, list specific changes.
        """
        review = call_llm(prompt_review, "mistral", "mistral-large-latest", KEYS["mistral"])
        
        if "APPROVED" in review.upper():
            return draft
        else:
            # Simple refinement loop
            print("--- [EXAM COUNCIL] Refining Draft ---")
            fix_prompt = f"""Refine this exam based on feedback.
            Draft: {draft}
            Feedback: {review}
            Output FINAL EXAM text only.
            """
            final_draft = call_llm(fix_prompt, "deepseek", "deepseek-chat", KEYS["deepseek"])
            return final_draft

    def _parallel_consult(self, prompt: str) -> str:
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_member = {
                executor.submit(call_llm, prompt, m["family"], m["model"], m["key"]): m["name"] for m in COUNCIL_MEMBERS
            }
            for future in as_completed(future_to_member):
                try:
                    results.append(f"--- Proposal by {future_to_member[future]} ---\n{future.result()}")
                except: pass
        return "\n".join(results)
