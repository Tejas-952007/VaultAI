import ollama

question = input("Enter your coding question: ")

response = ollama.chat(
    model="deepseek-coder:1.3b-instruct-q4_K_M",
    messages=[
        {
            "role": "user",
            "content": question
        }
    ]
)

print("\n===== DEEPSEEK CODING MODEL =====\n")
print(response["message"]["content"])