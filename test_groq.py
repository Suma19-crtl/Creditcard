from groq import Groq
from config import Config

client = Groq(
    api_key=Config.GROQ_API_KEY
)

try:

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": "Say hello in one sentence."
            }
        ],
        temperature=0.2
    )

    print("================================")
    print("✅ GROQ WORKING")
    print("================================")

    print(response.choices[0].message.content)

except Exception as e:

    print("================================")
    print("❌ GROQ FAILED")
    print("================================")

    print(type(e).__name__)
    print(str(e))