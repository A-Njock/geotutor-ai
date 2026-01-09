import re
from typing import List, Tuple, Dict, Callable, Optional
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

# Pedagogical prompt for COMPLEX calculations
PEDAGOGICAL_CALCULATION_TEMPLATE = """
**📚 PEDAGOGICAL APPROACH (Step-by-Step Learning):**
You are teaching a student. Structure your answer as follows:

## 1. 🎯 UNDERSTAND THE PROBLEM
- Restate what we're asked to find in simple terms
- Why is this important in geotechnical engineering?

## 2. 📋 IDENTIFY GIVEN DATA
List all known values with units:
- Parameter = Value (Unit) — what does this represent?

## 3. 🔬 SELECT THE METHOD
- Which formula/method applies? (e.g., Terzaghi, Meyerhof, Rankine)
- WHY does this method apply here? (explain the assumptions)
- Cite the source (textbook, code, context)

## 4. ✍️ SET UP THE EQUATION
- Write the general equation with variable names
- Explain what each term means

## 5. 🧮 SOLVE STEP-BY-STEP
- Substitute values one step at a time
- Use CALCULATE() for EVERY numerical operation
- Show intermediate results clearly

## 6. ✅ VERIFY & INTERPRET
- Does the result make physical sense?
- Typical range for this type of calculation?
- Safety factor considerations?

## 7. 📝 FINAL ANSWER
State the result clearly with:
- Value + Units
- Engineering interpretation
- Any recommendations or cautions

**Remember: A student should be able to learn the METHOD by reading your answer.**
"""

# Pedagogical prompt for SIMPLE educational questions
PEDAGOGICAL_EDUCATIONAL_TEMPLATE = """
**📚 PEDAGOGICAL APPROACH (Clear Explanation):**
You are teaching a student. Structure your answer as follows:

## 🎯 CORE CONCEPT
- Start with a clear, simple definition
- Use an everyday analogy if helpful

## 🔬 HOW IT WORKS
- Explain the mechanism or principle
- Use bullet points for clarity

## 📊 KEY FORMULAS (if applicable)
- Present any relevant equations
- Explain what each variable means

## 🌍 REAL-WORLD APPLICATIONS
- Where do we encounter this in practice?
- Give 1-2 concrete examples

## ⚠️ COMMON MISCONCEPTIONS
- What do students often get wrong?
- Clarify any tricky points

## 🔗 RELATED CONCEPTS
- Briefly mention connected topics for further study

**Keep it clear, concise, and memorable. Use diagrams in your mind to explain visually.**
"""

def classify_query_complexity(query: str) -> str:
    """
    Classifies a query as 'calculation' or 'educational' based on keywords.
    Returns: 'calculation' or 'educational'
    """
    q = query.lower()
    
    # Strong calculation indicators
    calculation_keywords = [
        "calculate", "compute", "determine", "find the", "what is the value",
        "given", "=", "kn", "kpa", "m²", "m³", "footing", "bearing capacity",
        "settlement", "factor of safety", "fs", "design", "size", "depth",
        "pressure", "stress", "strain", "load", "force", "moment"
    ]
    
    # Strong educational indicators
    educational_keywords = [
        "what is", "define", "explain", "describe", "why", "how does",
        "difference between", "compare", "types of", "classification",
        "principle", "theory", "concept", "meaning", "importance"
    ]
    
    calc_score = sum(1 for k in calculation_keywords if k in q)
    edu_score = sum(1 for k in educational_keywords if k in q)
    
    # Numbers and units strongly suggest calculation
    import re
    if re.search(r'\d+\.?\d*\s*(m|kn|kpa|mpa|kg|cm|mm)\b', q, re.IGNORECASE):
        calc_score += 3
    
    return "calculation" if calc_score > edu_score else "educational"


# Type alias for progress callback
# Callback receives: (stage: str, agent: str, status: str, detail: Optional[str])
ProgressCallback = Callable[[str, str, str, Optional[str]], None]

class ConsensusManager:
    def __init__(self, on_progress: Optional[ProgressCallback] = None):
        """
        Initialize ConsensusManager with optional progress callback.
        
        Args:
            on_progress: Callback function that receives progress updates.
                        Signature: (stage, agent, status, detail) -> None
                        - stage: "collecting" | "ranking" | "synthesizing"
                        - agent: Agent name (e.g., "Member_GPT") or "system"
                        - status: "started" | "done" | "error"
                        - detail: Optional additional info
        """
        self.on_progress = on_progress
    
    def _emit(self, stage: str, agent: str, status: str, detail: Optional[str] = None):
        """Emit a progress event if callback is registered."""
        if self.on_progress:
            try:
                self.on_progress(stage, agent, status, detail)
            except Exception as e:
                print(f"[WARN] Progress callback error: {e}")

    def stage1_collect_responses(self, query: str, context: str) -> Dict[str, str]:
        """
        Stage 1: Parallel generation of solutions.
        Returns: {member_name: solution_text}
        """
        print("--- [CONSENSUS] Stage 1: Collecting Responses ---")
        self._emit("collecting", "system", "started", f"Starting Stage 1 with {len(COUNCIL_MEMBERS)} agents")
        
        # Classify query to select appropriate pedagogical approach
        query_type = classify_query_complexity(query)
        print(f"    Query classified as: {query_type.upper()}")
        
        # Select pedagogical template based on query type
        if query_type == "calculation":
            pedagogical_approach = PEDAGOGICAL_CALCULATION_TEMPLATE
            task_instructions = """
Task: Solve this geotechnical engineering problem step-by-step.

**Context-Based Learning:**
1. Review the CONTEXT below for relevant formulas, solved examples, and code references.
2. If similar solved exercises exist, ANALYZE and FOLLOW their method as precedent.
3. Cite specific sources, subsections, or clauses that justify your approach.
4. Use CALCULATE() for ALL numerical computations.
"""
        else:
            pedagogical_approach = PEDAGOGICAL_EDUCATIONAL_TEMPLATE
            task_instructions = """
Task: Explain this geotechnical concept clearly for a student.

**Teaching Approach:**
1. Start with intuition before formulas.
2. Use analogies to everyday experiences when helpful.
3. Reference the CONTEXT for supporting material.
4. Make it memorable and understandable.
"""
        
        # Core pedagogical mission that applies to ALL responses
        PEDAGOGICAL_CORE = """
**🎓 CORE EDUCATIONAL MISSION (ALWAYS APPLIES):**
Your PRIMARY goal is to TEACH, not just answer. Every response must:
- Help the student UNDERSTAND the underlying principles
- Build their ability to solve SIMILAR problems independently  
- Use clear, accessible language (avoid jargon without explanation)
- Connect theory to practical engineering applications
- Encourage critical thinking ("Why does this work?")

A great answer is one where the student learns the METHOD, not just the result.
"""
        
        prompt = f"""You are a senior geotechnical engineer AND an excellent teacher.
Your goal is to help students LEARN, not just get answers.

{PEDAGOGICAL_CORE}

**RETRIEVED CONTEXT** (reference materials):
{context}

{CALCULATOR_TOOL_INSTRUCTIONS if query_type == "calculation" else ""}

{pedagogical_approach}

{task_instructions}

**Question:** {query}
"""
        
        responses = {}
        
        # Emit that each agent is starting
        for m in COUNCIL_MEMBERS:
            self._emit("collecting", m["name"], "started", f"Generating solution using {m['model']}")
        
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
                    self._emit("collecting", member_name, "done", "Solution submitted")
                except Exception as e:
                    print(f" ! {member_name} failed: {e}")
                    responses[member_name] = f"Error: {e}"
                    self._emit("collecting", member_name, "error", str(e))
                    
        self._emit("collecting", "system", "done", f"Collected {len(responses)} responses")
        return responses


    def stage2_collect_rankings(self, responses: Dict[str, str]) -> Tuple[List[dict], Dict[str, str]]:
        """
        Stage 2: Peer Review.
        Anonymizes responses and asks each model to rank them.
        Returns: (list_of_rankings, label_map)
        """
        print("--- [CONSENSUS] Stage 2: Peer Evaluation ---")
        self._emit("ranking", "system", "started", "Starting peer evaluation")
        
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
            self._emit("ranking", "system", "error", "No valid responses to rank")
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
        
        # Emit that each agent is starting to rank
        for m in COUNCIL_MEMBERS:
            self._emit("ranking", m["name"], "started", "Evaluating solutions")
        
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
                    self._emit("ranking", reviewer, "done", f"Ranked: {' > '.join(parsed)}" if parsed else "Ranking parsed")
                except Exception as e:
                    print(f" ! {reviewer} ranking failed: {e}")
                    self._emit("ranking", reviewer, "error", str(e))
                    
        self._emit("ranking", "system", "done", f"Received {len(rankings)} rankings")
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
        self._emit("synthesizing", "system", "started", "Aggregating votes and synthesizing answer")
        
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
        self._emit("synthesizing", winner_member, "started", f"Selected as winner (Solution {winner_label})")
        
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
        
        self._emit("synthesizing", "Chair", "started", "Drafting final answer")
        
        # Chair uses DeepSeek (or strongest model)
        final_res = call_llm(
            prompt=chair_prompt, 
            model_family="deepseek", 
            model_name="deepseek-chat", 
            api_key=KEYS["deepseek"]
        )
        
        self._emit("synthesizing", "Chair", "done", "Final answer ready")
        self._emit("synthesizing", "system", "done", "Consensus complete")
        
        return final_res

if __name__ == "__main__":
    # Test with a simple callback that prints progress
    def print_progress(stage, agent, status, detail):
        print(f"[PROGRESS] {stage} | {agent} | {status} | {detail}")
    
    cm = ConsensusManager(on_progress=print_progress)
    qs = "What is the bearing capacity of a prompt footing? B=2m, Gamma=18, phi=30."
    ctx = "Reference: Terzaghi (1943). Nq=22.5, Ngamma=19.7 for phi=30."
    
    r = cm.stage1_collect_responses(qs, ctx)
    ranks, lmap = cm.stage2_collect_rankings(r)
    final = cm.stage3_synthesize_final(qs, r, ranks, lmap)
    print("\nFINAL ANSWER:\n", final)
