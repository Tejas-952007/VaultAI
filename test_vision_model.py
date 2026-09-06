import ollama

image_path = input("Enter the image path: ").strip().strip('"')
question = input("Enter your question about the image: ")

response = ollama.chat(
    model="qwen3-vl:8b",
    messages=[
        {
            "role": "user",
            "content": question,
            "images": [image_path]
        }
    ]
)

print("\n===== QWEN3-VL VISION MODEL =====\n")
print(response["message"]["content"])