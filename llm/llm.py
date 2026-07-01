from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def generate_response(messages: list[dict], system: str = "") -> str:

    chat_messages = []

    if system:
        chat_messages.append(
            {
                "role": "system",
                "content": system
            }
        )

    chat_messages.extend(messages)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=chat_messages,
        temperature=0.7,
        max_tokens=1024,
    )

    return response.choices[0].message.content