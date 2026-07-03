from langchain_ollama import OllamaLLM
from .prompts import email_analysis_prompt

llm = OllamaLLM(model="llama3")

analysis_chain = email_analysis_prompt | llm
