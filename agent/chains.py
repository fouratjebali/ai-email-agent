from types import SimpleNamespace

try:
    from langchain_ollama import OllamaLLM
    from .prompts import email_analysis_prompt
except ImportError:
    OllamaLLM = None
    email_analysis_prompt = None


if OllamaLLM is not None and email_analysis_prompt is not None:
    llm = OllamaLLM(model="llama3")
    analysis_chain = email_analysis_prompt | llm
else:
    llm = None
    analysis_chain = None


class EmailChains:
    def __init__(self):
        self.analysis_chain = analysis_chain

    def _missing_dependency(self):
        raise RuntimeError(
            "LangChain/Ollama dependencies are not installed. Install requirements.txt to use EmailChains."
        )

    def classify(self, *args, **kwargs):
        if self.analysis_chain is None:
            self._missing_dependency()
        self._missing_dependency()

    def prioritize(self, *args, **kwargs):
        if self.analysis_chain is None:
            self._missing_dependency()
        self._missing_dependency()

    def summarize(self, *args, **kwargs):
        if self.analysis_chain is None:
            self._missing_dependency()
        self._missing_dependency()

    def suggest_reply(self, *args, **kwargs):
        if self.analysis_chain is None:
            self._missing_dependency()
        self._missing_dependency()
