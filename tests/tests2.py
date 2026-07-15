import json
from agent_validator.agent_validator import ResponseValidatorAgent


validator = ResponseValidatorAgent()

original_email = """
Hello,

I would like to know the status of my order.

Thank you.
"""

generated_response = """
Hello,

Thank you for your email.
Your order has been shipped and should arrive within 3 business days.

Best regards,
Customer Support
"""

result = validator.validate(
    original_email=original_email,
    generated_response=generated_response,
    email_id="EMAIL_001"
)

print(json.dumps(result, indent=4))
