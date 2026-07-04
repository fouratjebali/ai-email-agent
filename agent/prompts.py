# ----------------------------------------------------------
# PROMPT 6 : GÉNÉRATION BULK EMAIL PERSONNALISÉ
# ----------------------------------------------------------
BULK_PERSONALIZED_PROMPT = """
You are an expert professional email writer.
You must write a PERSONALIZED email for ONE specific recipient.

Recipient details:
- Name    : {name}
- Email   : {email}
- Role    : {role}
- Context : {context}

General topic / purpose of the email:
{topic}

Additional instructions:
{instructions}

STRICT RULES:
- Write ONLY for THIS recipient, using their specific context.
- Personalize: mention their name, role, and specific context.
- Do NOT write a generic email that could fit anyone.
- Language: write in French unless specified otherwise.
- Length: 4-6 sentences, professional tone.
- Respond ONLY with valid JSON, no markdown, no extra text.

JSON response:
{{
  "subject": "personalized subject line",
  "body": "complete personalized email body with greeting and signature",
  "personalization_note": "what was personalized for this recipient"
}}
"""

# ----------------------------------------------------------
# PROMPT 7 : RÉSUMÉ DE CONVERSATION
# ----------------------------------------------------------
CONVERSATION_SUMMARY_PROMPT = """
You are summarizing a conversation between a user and an AI email assistant.

Conversation history:
{history}

Create a concise summary that captures:
1. What emails were read/analyzed
2. What actions were taken (sent, classified, etc.)
3. Any important email IDs or recipients mentioned
4. Current context/state

Respond ONLY with valid JSON:
{{
  "summary": "2-3 sentence summary",
  "emails_processed": ["list of email subjects or IDs"],
  "actions_taken": ["list of actions"],
  "pending_actions": ["list of things not yet done"]
}}
"""