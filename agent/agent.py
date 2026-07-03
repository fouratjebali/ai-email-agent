from langchain.agents import initialize_agent, Tool
from langchain_ollama import OllamaLLM
from .chains import analysis_chain, reply_chain, summary_chain
llm = OllamaLLM(model="llama3")
tools = [
    Tool(
        name="Analyze Email",
        func=analysis_chain.invoke,
        description="Analyse un email et donne sujet, priorité, résumé et réponse"
    ),

    Tool(
        name="Reply Email",
        func=reply_chain.invoke,
        description="Génère une réponse professionnelle pour un email"
    ),

    Tool(
        name="Summary Email",
        func=summary_chain.invoke,
        description="Résume un email en une seule phrase"
    )
]
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)
