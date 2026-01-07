import re
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import call_llm, KEYS
from ..tools.calculator import process_calculations

# Architecture:
# We will use 3 distinct "personas" or models for the Council.
#Ideally different models, but for now we use the ones available in KEYS.
COUNCIL_MEMBERS = [
    {"name": "Member_DeepSeek", "family": "deepseek", "model": "deepseek-chat", "key": KEYS["deepseek"]},
    {"name": "Member_GPT", "family": "gpt", "model": "gpt-4o", "key": KEYS["gpt"]},
    {"name": "Member_Mistral", "family": "mistral", "model": "mistral-large-latest", "key": KEYS["mistral"]}
]

# Calculator tool instructions to inject into prompts
CALCULATOR_TOOL_INSTRUCTIONS = """
**IMPORTANT - CALCULATOR TOOL:**
For ANY numerical calculation, you MUST use the CALCULATE() function.
Format: CALCULATE(expression)

Examples:
- CALCULATE(22.5 * 18 * 1.5) → computes to exact value
- CALCULATE(tan(radians(30))) → computes tan of 30 degrees
- CALCULATE(sqrt(2) * 100) → computes √2 × 100

Available functions: sin, cos, tan, asin, acos, atan, sqrt, exp, log, log10, radians, degrees, pi, e, abs, round, min, max, pow

DO NOT do mental math. ALWAYS wrap numerical computations in CALCULATE().
"""

class ConsensusManager:
    def __init__(self):
        pass

    def stage1_collect_responses(self, query: str, context: str) -> Dict[str, str]:
        """
        Stage 1: Parallel generation of solutions.
        Returns: {member_name: solution_text}
        """
        print("--- [CONSENSUS] Stage 1: Collecting Responses ---")
        prompt = f"""You are a senior geotechnical engineer.
        First, review the RETRIEVED CONTEXT below. It may contain:
        - Relevant Theory/Formulas
        - Similar Solved Exercises (with solutions)
        - Applicable Codes (Eurocode, ASTM)
        - Specific Subsections/Clauses
        
        Context:
        {context}
        
        {CALCULATOR_TOOL_INSTRUCTIONS}
        
        Task:
        Solve the following problem. 
        1. Identify the specific SUBSECTIONS or CLAUSES in the context that define the rules for this problem.
        2. If similar solved exercises are present in the context, ANALYZE THEM. Use their method as a precedent.
        3. Discuss WHY the referenced subsection applies to the specific user request details.
        4. Cite the theory/source from the context.
        5. Show your steps, calculations, and final result cleanly.
        6. USE CALCULATE() for ALL numerical computations to ensure accuracy.
        
        Problem: {query}
        """
        
        responses = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_member = {
                executor.submit(
                    call_llm, 
                    prompt=prompt, 
                    model_family=m["family"], 
                    model_name=m["model"], 
                    api_key=m["key"]
                ): m["name"] for m in COUNCIL_MEMBERS
            }
            
            for future in as_completed(future_to_member):
                member_name = future_to_member[future]
                try:
                    res = future.result()
                    # Process CALCULATE() patterns in the response
                    processed_res = process_calculations(res)
                    responses[member_name] = processed_res
                    print(f" > {member_name} submitted solution.")
                except Exception as e:
                    print(f" ! {member_name} failed: {e}")
                    responses[member_name] = f"Error: {e}"
                    
        return responses


    def stage2_collect_rankings(self, responses: Dict[str, str]) -> Tuple[List[dict], Dict[str, str]]:
        """
        Stage 2: Peer Review.
        Anonymizes responses and asks each model to rank them.
        Returns: (list_of_rankings, label_map)
        """
        print("--- [CONSENSUS] Stage 2: Peer Evaluation ---")
        
        # 1. Anonymize
        labels = ["A", "B", "C", "D", "E"]
        label_map = {} # A -> Member_DeepSeek
        anonymized_text = ""
        
        valid_members = [m for m in responses.keys() if "Error" not in responses[m]]
        
        for i, member in enumerate(valid_members):
            label = labels[i]
            label_map[label] = member
            anonymized_text += f"\n--- SOLUTION {label} ---\n{responses[member]}\n"
            
        if not label_map:
            return [], {}

        # 2. Prompt for Ranking
        rank_prompt = f"""You are a technical reviewer for the Geotechnical Council.
        Review the following solutions and RANK them from BEST to WORST based on:
        - Accuracy of method (e.g. Terzaghi vs Vesic)
        - Correctness of calculation
        - Clarity
        
        Solutions:
        {anonymized_text}
        
        Output Format STRICTLY:
        FINAL RANKING: [Best Label] > [2nd Best] > ...
        CRITIQUE: [Brief explanation]
        """
        
        rankings = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # We ask the same Council Members to review
            future_to_member = {
                executor.submit(
                    call_llm, 
                    prompt=rank_prompt, 
                    model_family=m["family"], 
                    model_name=m["model"], 
                    api_key=m["key"]
                ): m["name"] for m in COUNCIL_MEMBERS
            }
            
            for future in as_completed(future_to_member):
                reviewer = future_to_member[future]
                try:
                    res = future.result()
                    parsed = self.parse_ranking(res)
                    
                    # Debug: Print raw response if parsing failed
                    if not parsed:
                        print(f"   [DEBUG] {reviewer} raw response (first 400 chars):")
                        print(f"   {res[:400]}...")
                    
                    rankings.append({
                        "reviewer": reviewer,
                        "raw_text": res,
                        "parsed_order": parsed
                    })
                    print(f" > {reviewer} submitted ranking: {parsed}")
                except Exception as e:
                    print(f" ! {reviewer} ranking failed: {e}")
                    
        return rankings, label_map

    def parse_ranking(self, text: str) -> List[str]:
        """
        Extracts ['A', 'C', 'B'] from various formats:
        - "FINAL RANKING: A > C > B"
        - "1. A, 2. C, 3. B"
        - "Best: A, Second: B, Third: C"
        - "A, B, C" (simple comma list)
        """
        valid_labels = {"A", "B", "C", "D", "E"}
        
        try:
            # Pattern 1: FINAL RANKING: A > C > B (or with →, -, etc.)
            match = re.search(r"FINAL\s*RANKING[:\s]*([A-E][\s\>\-→,A-E]+)", text, re.IGNORECASE)
            if match:
                raw_seq = match.group(1)
                tokens = re.split(r"[\>\-→,\s]+", raw_seq)
                clean_tokens = [t.strip().upper() for t in tokens if t.strip().upper() in valid_labels]
                if clean_tokens:
                    return clean_tokens
            
            # Pattern 2: Numbered list "1. A" or "1) A" or "1: A"
            numbered = re.findall(r"[1-5][\.\)\:]\s*\*?\*?([A-E])\*?\*?", text, re.IGNORECASE)
            if numbered:
                clean_tokens = [t.upper() for t in numbered if t.upper() in valid_labels]
                if clean_tokens:
                    return clean_tokens
            
            # Pattern 3: "Best: A" or "First: B" style
            ordinal_match = re.findall(r"(?:best|first|1st|second|2nd|third|3rd|worst|last)[:\s]+\*?\*?([A-E])\*?\*?", text, re.IGNORECASE)
            if ordinal_match:
                clean_tokens = [t.upper() for t in ordinal_match if t.upper() in valid_labels]
                if clean_tokens:
                    return clean_tokens
            
            # Pattern 4: Solution ranking "Solution A is best" pattern
            solution_match = re.findall(r"Solution\s+([A-E])", text, re.IGNORECASE)
            if solution_match:
                clean_tokens = [t.upper() for t in solution_match if t.upper() in valid_labels]
                if clean_tokens:
                    return clean_tokens
            
            # Pattern 5: Simple sequence A > B > C or A, B, C anywhere in text
            simple_seq = re.search(r"([A-E])\s*[\>\-→,]\s*([A-E])(?:\s*[\>\-→,]\s*([A-E]))?", text, re.IGNORECASE)
            if simple_seq:
                clean_tokens = [g.upper() for g in simple_seq.groups() if g and g.upper() in valid_labels]
                if clean_tokens:
                    return clean_tokens
            
            # Pattern 6: Last resort - find any standalone A, B, C mentions in ranking context
            if "rank" in text.lower() or "best" in text.lower() or "order" in text.lower():
                # Find all single letter labels that appear standalone
                all_labels = re.findall(r"\b([A-E])\b", text)
                # Deduplicate while preserving order
                seen = set()
                clean_tokens = []
                for lbl in all_labels:
                    if lbl.upper() not in seen and lbl.upper() in valid_labels:
                        seen.add(lbl.upper())
                        clean_tokens.append(lbl.upper())
                if clean_tokens:
                    return clean_tokens
            
            return []
        except Exception:
            return []

    def stage3_synthesize_final(self, query: str, responses: Dict[str, str], rankings: List[dict], label_map: Dict[str, str]) -> str:
        """
        Stage 3: The Chair synthesizes the final answer based on the winner.
        """
        print("--- [CONSENSUS] Stage 3: Synthesis ---")
        
        # Simple aggregation: Vote counting (Borda count or simple winner)
        # Using simple winner for V1
        scores = {label: 0 for label in label_map.keys()}
        
        for r in rankings:
            order = r["parsed_order"]
            for i, label in enumerate(order):
                # Points: 3 for 1st, 2 for 2nd...
                points = max(0, 3 - i)
                if label in scores:
                    scores[label] += points
                    
        # Find winner
        winner_label = max(scores, key=scores.get) if scores else None
        winner_member = label_map.get(winner_label, "Unknown")
        print(f" > Winner based on aggregation: Solution {winner_label} (by {winner_member})")
        
        best_solution = responses.get(winner_member, "")
        
        # Chair produces final output
        chair_prompt = f"""You are the Chair of the Council.
        The Council has debated and selected Solution {winner_label} as the best.
        
        User Query: {query}
        
        Winning Solution ({winner_label}):
        {best_solution}
        
        Peer Comments:
        {chr(10).join([r['reviewer'] + ': ' + r['raw_text'][:200] + '...' for r in rankings])}
        
        Task:
        Synthesize the FINAL, definitive answer. 
        Correct any minor issues noted by peers if necessary.
        Format cleanly as a final report.
        """
        
        # Chair uses DeepSeek (or strongest model)
        final_res = call_llm(
            prompt=chair_prompt, 
            model_family="deepseek", 
            model_name="deepseek-chat", 
            api_key=KEYS["deepseek"]
        )
        
        return final_res

if __name__ == "__main__":
    # Test
    cm = ConsensusManager()
    qs = "What is the bearing capacity of a prompt footing? B=2m, Gamma=18, phi=30."
    ctx = "Reference: Terzaghi (1943). Nq=22.5, Ngamma=19.7 for phi=30."
    
    r = cm.stage1_collect_responses(qs, ctx)
    ranks, lmap = cm.stage2_collect_rankings(r)
    final = cm.stage3_synthesize_final(qs, r, ranks, lmap)
    print("\nFINAL ANSWER:\n", final)
