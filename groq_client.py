from groq import Groq
from config import Config


client = Groq(
    api_key=Config.GROQ_API_KEY
)


def ask_ai(prompt):

    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": """
You are the AI assistant inside a Credit Card Fraud Detection
web application called FraudShield AI.

Your job is to help users understand:
- Credit card fraud
- Fraud detection
- Machine learning
- Transaction risk
- Confidence scores
- Fraud prevention
- Cybersecurity
- Dashboard statistics
- This application's features

IMPORTANT RESPONSE STYLE:

1. Be conversational and friendly.
2. Answer simple questions simply.
3. Do NOT give long academic answers unless the user specifically
   asks for a detailed explanation.
4. For normal questions, keep the response around 2-6 sentences.
5. Use bullet points only when they make the answer easier to read.
6. Avoid large tables unless the user specifically asks for one.
7. Do not automatically create headings such as "Executive Summary"
   for normal questions.
8. Explain technical concepts in simple language suitable for an
   MCA student.
9. If the user asks a general question unrelated to fraud detection,
   answer it normally and briefly.
10. If the user asks for a detailed explanation, assignment answer,
    exam answer, or report, then provide more detail.
11. Never claim that you personally analyzed a transaction unless
    transaction information was actually provided.
12. Never invent prediction results, fraud probabilities, or
    dashboard statistics.

The user may ask very simple questions. Match the length and
complexity of your answer to the user's question.
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.4
        )

        return response.choices[0].message.content


    except Exception as e:

        print("======================================")
        print("❌ GROQ API ERROR")
        print("Error Type:", type(e).__name__)
        print("Error:", str(e))
        print("======================================")

        raise