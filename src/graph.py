from typing import TypedDict, Annotated, List, Union, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .agents.consensus import ConsensusManager
from .agents.librarian import LibrarianAgent
from .agents.critic import CriticAgent
from .agents.exam_council import ExamCouncil
from .tools.visualizer import Visualizer
from .tools.formatter import ExamFormatter

from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# 1. Define State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    context: str
    plan: str
    code: str
    result: str
    critique: str
    next_step: str
    mindmap_path: str

# 2. Init Agents
librarian = LibrarianAgent()
consensus = ConsensusManager()
critic = CriticAgent()
exam_council = ExamCouncil()
visualizer = Visualizer()
formatter = ExamFormatter()

# 3. Define Nodes

def librarian_node(state: AgentState):
    query = state['messages'][0].content
    context = librarian.retrieve(query)
    msg = AIMessage(content=f"Librarian: Retrieved context.", name="librarian")
    return {"context": context, "messages": [msg]}

def router_node(state: AgentState):
    # Simple keyword routing
    query = state['messages'][0].content.lower()
    if "exam" in query:
        return {"next_step": "exam"}
    return {"next_step": "consensus"}

def exam_node(state: AgentState):
    query = state['messages'][0].content
    context = state.get('context', '')
    
    # 1. Design & Draft
    exam_text = exam_council.design_exams(query, context)
    
    # 2. Format
    file_path = formatter.create_exam_docx(exam_text)
    
    result = f"Exam Generated successfully.\nFile saved at: {file_path}\n\nPreview:\n{exam_text[:500]}..."
    msg = AIMessage(content=result, name="exam_council")
    return {"result": result, "messages": [msg]}

def consensus_node(state: AgentState):
    query = state['messages'][0].content
    context = state.get('context', '')
    
    # 3-Stage Consensus
    responses = consensus.stage1_collect_responses(query, context)
    rankings, label_map = consensus.stage2_collect_rankings(responses)
    final_answer = consensus.stage3_synthesize_final(query, responses, rankings, label_map)
    
    # Mind Map Check
    mindmap_path = None
    if "theory" in query.lower() or "concept" in query.lower() or "explain" in query.lower():
        try:
            # New API: generate_mindmap returns the image path directly
            mindmap_path = visualizer.generate_mindmap(query, final_answer)
            final_answer += f"\n\n### Concept Map\n![Mindmap]({mindmap_path})\n*(Image saved to: {mindmap_path})*"
        except Exception as e:
            print(f"[WARN] Mindmap rendering failed: {e}")
    
    msg = AIMessage(content=f"Consensus Council: {final_answer}", name="council")
    return {"result": final_answer, "plan": "Consensus Reached", "code": "Multi-agent generated", "messages": [msg], "mindmap_path": mindmap_path if mindmap_path else ""}

def critic_node(state: AgentState):
    query = state['messages'][0].content
    result = state['result']
    critique = critic.review(query, "Consensus Plan", "N/A", result)
    msg = AIMessage(content=f"Critic: {critique}", name="critic")
    return {"critique": critique, "messages": [msg]}

# 4. Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("librarian", librarian_node)
workflow.add_node("router", router_node)
workflow.add_node("consensus", consensus_node)
workflow.add_node("exam", exam_node)
workflow.add_node("critic", critic_node)

# Edges
workflow.set_entry_point("librarian")
workflow.add_edge("librarian", "router")

workflow.add_conditional_edges(
    "router",
    lambda x: x['next_step'],
    {
        "exam": "exam",
        "consensus": "consensus"
    }
)

workflow.add_edge("consensus", "critic")
workflow.add_edge("critic", END)
workflow.add_edge("exam", END) # Exam generation ends flow (no critic needed for formatting)

app = workflow.compile()
