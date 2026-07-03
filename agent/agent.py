from langchain.agents import initialize_agent
from langchain_ollama import OllamaLLM
from .tools import tools
llm = OllamaLLM(model="llama3")
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)
if __name__ == "__main__":
    result = agent.run(
        "Lis mes emails et fais un résumé"
    )
    print("RESULT:\n", result)
