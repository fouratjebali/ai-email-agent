from typing import Annotated, TypedDict
from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from agent.tools import ALL_TOOLS
from config.settings import settings

# 1. Définir l'état du graphe
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# 2. Prompt système de l'agent
SYSTEM_PROMPT = """You are an intelligent email management assistant with access to Gmail.

You have the following tools available:
- read_emails        : read emails from Gmail (use this first)
- classify_email     : classify an email by category
- prioritize_email   : determine urgency level
- summarize_email    : generate a short summary
- suggest_reply      : generate a professional reply
- send_single_email  : send one email
- send_bulk_email    : send personalized emails to multiple recipients
- get_urgent_emails  : find all urgent emails automatically

IMPORTANT RULES:
1. Always call read_emails first before any analysis.
2. Use email IDs from read_emails results to call other tools.
3. For bulk sending, generate personalized content for EACH recipient.
4. Before sending any email, always show the content to the user.
5. Think step by step. Use one tool at a time.
6. Respond in the same language the user wrote to you.
7. After completing a task, give a clear summary of what was done.
"""


# 3. Construire le graphe LangGraph
class EmailAgent:
    def __init__(self):
        # LLM avec les outils bindés
        self.llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.1,
        )

        # Binder les outils au LLM
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)

        # Construire le graphe
        self.graph = self._build_graph()

    def _agent_node(self, state: AgentState) -> AgentState:
        # Ajouter le système prompt au début si c'est le premier appel
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def _build_graph(self) -> StateGraph:
        # Créer le graphe avec notre état
        graph_builder = StateGraph(AgentState)

        # Nœud 1 : l'agent (LLM qui décide)
        graph_builder.add_node("agent", self._agent_node)

        # Nœud 2 : les outils (exécution des tools)
        tool_node = ToolNode(tools=ALL_TOOLS)
        graph_builder.add_node("tools", tool_node)

        # Point d'entrée
        graph_builder.add_edge(START, "agent")

        # Après l'agent : aller aux tools OU terminer
        graph_builder.add_conditional_edges(
            "agent",
            tools_condition,   # vérifie si le LLM a demandé un tool call
        )

        # Après les tools : toujours revenir à l'agent
        graph_builder.add_edge("tools", "agent")

        return graph_builder.compile()

    def run(self, instruction: str) -> str:
        initial_state = {
            "messages": [HumanMessage(content=instruction)]
        }

        final_state = self.graph.invoke(
            initial_state,
            config={"recursion_limit": 25},  # max 25 itérations
        )

        # Retourner le dernier message de l'agent
        last_message = final_state["messages"][-1]
        return last_message.content

    def stream(self, instruction: str):
        initial_state = {
            "messages": [HumanMessage(content=instruction)]
        }

        for event in self.graph.stream(
            initial_state,
            config={"recursion_limit": 25},
        ):
            for node_name, state_update in event.items():
                messages = state_update.get("messages", [])
                for msg in messages:
                    yield node_name, msg