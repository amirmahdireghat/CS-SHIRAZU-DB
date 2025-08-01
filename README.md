🤖 Telegram AI Chatbot with OpenAI, SQLite & Zarinpal
A smart, lightweight Telegram bot powered by OpenAI's GPT API. It answers user questions, tracks conversations with SQLite, and manages token-based payments via Zarinpal (an Iranian payment gateway).

✨ Features
AI-powered responses via OpenAI (ChatGPT)

User/conversation management with SQLite

Token-based access control

Zarinpal payment integration for token purchases

Simple, secure Telegram interaction

🧰 Tech Stack
Component	Technology
Language	Python
Telegram Bot	python-telegram-bot or aiogram
AI Engine	OpenAI (GPT-3.5)
Database	SQLite
Payment System	Zarinpal API
Config & Security	dotenv (.env file)
📁 Project Structure
text
project-root/
│
├── bot.py            # Main bot entry point
├── db.py             # SQLite DB management
├── openai_api.py     # OpenAI request handling
├── payment.py        # Zarinpal payment integration
├── config.py         # Loads environment variables
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
🏁 Getting Started
1. Clone the Repository
bash
git clone https://github.com/amirmahdireghat/CS-SHIRAZU-DB.git
cd CS-SHIRAZU-DB
2. Install Dependencies
bash
pip install -r requirements.txt
3. Set Up Environment Variables
Create a .env file and add the following:

text
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
ZARINPAL_MERCHANT_ID=your_zarinpal_merchant_id
CALLBACK_URL=https://yourdomain.com/verify
4. Run the Bot
bash
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
timestamp	When message was created
🔁 How It Works
User starts the bot

Bot checks if the user exists in the database

If tokens are available, user sends a question

Bot fetches answer from OpenAI

Token is deducted, conversation is saved

If no tokens remain, user is prompted to pay via Zarinpal

Upon successful payment, new tokens are added

💸 Zarinpal Payment Integration
Users purchase tokens through a Zarinpal payment link

After successful payment verification, tokens are automatically credited to the user’s account

Local, secure, and Iran-compatible
