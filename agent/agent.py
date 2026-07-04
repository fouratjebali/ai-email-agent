from typing import Annotated, TypedDict
from urllib.error import URLError
from urllib.request import urlopen
from langchain_ollama import ChatOllama
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
SYSTEM_PROMPT = """You are an email assistant with Gmail tools.

Rules:
1. Use read_emails before any analysis.
2. Use the exact email IDs from tool output only.
3. Never invent placeholder IDs or paraphrase them.
4. If you need IDs, copy them verbatim from the JSON returned by read_emails.
5. Call exactly one tool per assistant turn.
6. Do not request classify_email, prioritize_email, summarize_email, or suggest_reply until after read_emails has returned real IDs.
7. Show email content before sending anything.
8. Reply in the user's language.
9. Keep responses concise and actionable.
"""


# 3. Construire le graphe LangGraph
class EmailAgent:
    def __init__(self):
        self._ensure_ollama_available()

        # LLM avec les outils bindés
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.1,
            num_predict=settings.OLLAMA_NUM_PREDICT,
            client_kwargs={"timeout": settings.OLLAMA_TIMEOUT_SECONDS},
        )

        # Binder les outils au LLM
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)

        # Construire le graphe
        self.graph = self._build_graph()

    def _ensure_ollama_available(self) -> None:
        health_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        try:
            with urlopen(health_url, timeout=3):
                return
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"Cannot reach Ollama at {settings.OLLAMA_BASE_URL}. Start Ollama or update OLLAMA_BASE_URL before running the agent."
            ) from exc

    def _agent_node(self, state: AgentState) -> AgentState:
        # Ajouter le système prompt au début si c'est le premier appel
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = self.llm_with_tools.invoke(messages)

        tool_calls = getattr(response, "tool_calls", [])
        if len(tool_calls) > 1:
            response = AIMessage(
                content=response.content,
                tool_calls=[tool_calls[0]],
                additional_kwargs=getattr(response, "additional_kwargs", {}),
                response_metadata=getattr(response, "response_metadata", {}),
                id=getattr(response, "id", None),
            )

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