from ollama import chat
response = chat(
    model="qwen3.5",
    messages=[
        {
        "role":"user",
        "content": "Explain what is refinery is in one sentence."
        }
    ]
)
print(response.message.content)