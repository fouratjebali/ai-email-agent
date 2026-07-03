from langchain_core.prompts import PromptTemplate

# Prompt pour analyser un email
email_analysis_prompt = PromptTemplate.from_template("""
Tu es un assistant intelligent spécialisé dans l'analyse des emails.

Analyse l'email suivant :

{email}

Réponds sous le format suivant :

Sujet :
Priorité : (Urgente / Normale / Faible)
Résumé :
Réponse proposée :
""")

# Prompt pour générer uniquement une réponse
reply_prompt = PromptTemplate.from_template("""
Tu es un assistant professionnel.

Rédige une réponse polie et professionnelle à cet email :

{email}
""")

# Prompt pour résumer un email
summary_prompt = PromptTemplate.from_template("""
Résume cet email en une seule phrase :

{email}
""")
