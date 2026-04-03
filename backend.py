from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import sqlite3

app = Flask(__name__)
CORS(app)

# 🧠 Load AI model
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

chat_history_ids = None

# 🥇 SMART ANSWERS (IMPORTANT)
def smart_reply(user_input):
    text = user_input.lower()

    if "what is ai" in text:
        return "Artificial Intelligence is a technology that enables machines to think, learn, and make decisions like humans."

    elif "machine learning" in text:
        return "Machine learning is a part of AI where systems learn from data and improve automatically."

    elif "python" in text:
        return "Python is a powerful programming language used for web development, AI, and data science."

    elif "who are you" in text:
        return "I am Jarvis, your AI assistant. I can help answer questions and assist you."

    elif "joke" in text:
        return "Why did the computer go to the doctor? Because it caught a virus!"

    return None

# 🧠 AI RESPONSE (FIXED)
def get_response(user_input):
    global chat_history_ids

    prompt = f"Answer clearly: {user_input}"

    new_input_ids = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors='pt')

    if chat_history_ids is not None:
        bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1)
    else:
        bot_input_ids = new_input_ids

    chat_history_ids = model.generate(
        bot_input_ids,
        max_length=500,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(
        chat_history_ids[:, bot_input_ids.shape[-1]:][0],
        skip_special_tokens=True
    )

    # 🛑 Fix repeating problem
    if response.strip().lower() == user_input.strip().lower():
        return "That's an interesting question. Let me explain it clearly."

    return response

# 💾 Save chat
def save_chat(user, message, response):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chats (user, message, response) VALUES (?, ?, ?)",
        (user, message, response)
    )
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return "Backend is running 🚀"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user = data.get("user", "guest")
    message = data.get("message")

    # 🥇 Try smart answers first
    reply = smart_reply(message)

    # 🥈 Then AI
    if not reply:
        reply = get_response(message)

    save_chat(user, message, reply)

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)