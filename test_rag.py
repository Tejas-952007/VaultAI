from ollama import chat

# THE INFORMATION RETRIEVED FROM OUR PDF
context = """
The refinery processes crude oil into useful products.
"""

# USER QUESTION
question = "What does a refinery produce?"

# ASK QWEN3.5 TO ANSWER USING THE CONTEXT
response = chat(
    model="qwen3.5",
    messages=[
        {
            "role": "user",
            "content": f"""
Answer the question using ONLY the information provided below.

Information:
{context}

Question:
{question}
"""
        }
    ]
)

# PRINT THE FINAL ANSWER
print("\nFINAL ANSWER:")
print(response.message.content)