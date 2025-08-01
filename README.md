# 🤖 Telegram AI Chatbot with OpenAI, SQLite & Zarinpal

A smart and lightweight Telegram bot powered by **OpenAI's GPT API** that answers user questions, tracks conversations using **SQLite**, and handles **token-based payment via Zarinpal** (an Iranian payment gateway).

---

## ✨ Features

- AI-powered responses via OpenAI (ChatGPT)
- User and conversation management with SQLite
- Token-based access control
- Zarinpal payment integration for purchasing tokens
- Simple, secure interaction through Telegram

---

## 🧰 Tech Stack

| Component       | Technology           |
|----------------|----------------------|
| Language        | Python               |
| Telegram Bot    | `python-telegram-bot` or `aiogram` |
| AI Engine       | OpenAI (GPT-3.5)     |
| Database        | SQLite               |
| Payment System  | Zarinpal API         |
| Config & Security | dotenv (`.env` file) |

---

## 📁 Project Structure

📦 project-root/
│
├── bot.py # Main bot entry point
├── db.py # SQLite DB management
├── openai_api.py # Handling OpenAI requests
├── payment.py # Zarinpal payment integration
├── config.py # Load environment variables
├── requirements.txt # Python dependencies
└── README.md # Project documentation

yaml
Copy
Edit

---

## 🏁 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/amirmahdireghat/CS-SHIRAZU-DB.git
cd CS-SHIRAZU-DB
2. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Set Up Environment Variables
Create a .env file and add the following:

ini
Copy
Edit
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
ZARINPAL_MERCHANT_ID=your_zarinpal_merchant_id
CALLBACK_URL=https://yourdomain.com/verify
4. Run the Bot
bash
Copy
Edit
python bot.py
🗃️ Database Schema
users Table
Column	Description
id	Primary Key (Auto ID)
telegram_id	User’s Telegram ID
token	Remaining token count
created_at	User registration time

messages Table
Column	Description
id	Primary Key
user_id	Foreign key from users table
question	User’s question
answer	AI-generated response
timestamp	When the message was created

🔁 How It Works
User starts the bot

Bot checks if the user exists in the database

If token is available, the user sends a question

Bot fetches the answer from OpenAI

Token is deducted, and conversation is saved

If no tokens remain, user is prompted to pay via Zarinpal

Upon successful payment, new tokens are added

💸 Zarinpal Payment Integration
Users can purchase tokens through a Zarinpal payment link

After payment verification, tokens are automatically added to the user’s account

Local, secure, and Iran-compatible

🔮 Future Improvements
Add support for multiple languages

Enable long-term memory (contextual chat)

Integrate Whisper API for voice messages

Create an admin dashboard for analytics and user management

Deploy on cloud services like Heroku or Render
