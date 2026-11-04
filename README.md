# BOLPAY💙 – Voice-First Digital Payment Assistant

BoloPay is a voice-first payment assistant designed to make digital payments easier, safer, and more accessible, especially for senior citizens and people who find traditional payment apps difficult to use.

Users can interact with BoloPay using voice commands in multiple Indian languages. The assistant understands requests, guides users through the payment process, and provides spoken responses.

🔗 **Live demo:** https://bolpay.streamlit.app/
🎥 **Demo video:** https://x.com/tanusri_alekhya/status/2117014165307146609
📄 **Solution pitch:** [SOLUTION_PITCH.md](SOLUTION_PITCH.md)
🏆 Built solo for the Great Indian AI Internship Challenge 2026 by Gnani.ai

> If the voice service is waking up, wait about 30 seconds and click the mic again.

## Features

- **Voice-based interaction:** Give commands using your voice instead of navigating multiple screens.
- **10 Indian languages:** English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati, and Punjabi.
- **Speech recognition:** Converts spoken commands into text using Gnani STT.
- **AI-powered assistant:** Understands user requests using Groq's GPT-OSS-20B model.
- **Text-to-speech:** Provides spoken responses using Gnani TTS.
- **Payment simulation:** Simulates sending money to recipients.
- **Wallet balance:** Displays the demo wallet balance.
- **PIN verification:** Requires PIN confirmation before completing a simulated payment.
- **Transaction history:** Displays previous simulated transactions.
- **Recipient selection:** Allows users to select a recipient or enter a 10-digit Indian mobile number.

## Technology Stack

```text
| Frontend --- Streamlit, HTML, CSS, JavaScript 
| Backend --- Python, FastAPI 
| Communication --- WebSocket 
| Speech-to-Text --- Gnani STT (Gnani Prisma V2.5)
| AI Model  --- GPT-OSS-20B (Groq)
| Text-to-Speech --- Gnani TTS (Gnani Timbre V3.0)
```

## Project Structure

```text
BoloPay/
│
├── main.py
├── backend.py
├── i18n.py
├── translations.json
├── requirements.txt
├── .env
│
├── knowledge/
│   └── bolopay_knowledge.txt
│
└── voice_component/
    └── index.html
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/tanusrialekhya/BOLOPAY-
cd BoloPay
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project directory and add your API credentials:

```env
GROQ_API_KEY=your_groq_api_key
GNANI_STT_API_KEY=your_gnani_stt_api_key
GNANI_TSS_API_KEY=your_gnani_tss_api_key
```

Use the exact environment variable names expected by your backend. Never upload real API keys or secrets to GitHub.

### 4. Start the FastAPI backend

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000
```

### 5. Start the Streamlit frontend

Open another terminal and run:

```bash
streamlit run main.py
```

Open the local URL displayed in your terminal to use BoloPay.

## Demo Information

BoloPay currently uses a simulated wallet and payment system for demonstration and testing.

- Starting demo balance: ₹10,000
- Demo PIN: 7777
- Payments are simulated and do not transfer real money.
- No real bank account or UPI transaction is performed.

  ## What You Can Ask BoloPay

You can talk to BoloPay naturally, just like talking to another person. Here are some example voice commands you can try.

### 1. Send Money

- "Send ₹500 to Amma."
- "Send ₹1000 to Dad."
- "Pay ₹200 to Priya."
- "Send ₹750 to Rahul."
- "I want to send 500 rupees to my mother."
- "Pay 300 rupees to my friend."

### 2. Check Wallet Balance

- "What is my wallet balance?"
- "How much money do I have?"
- "Tell me my remaining balance."

### 3. Transaction History

- "Show my transaction history."
- "What was my last transaction?"
- "How much money did I send today?"
- "Show my recent payments."

### 4. Understand BoloPay

- "What is BolPay?"
- "How can I send money?"
- "How many languages can you speak?"
- "Which languages are supported?"
- "How do I check my balance?"

### 5. Change Language

- "Switch to Hindi."
- "Speak in Telugu."
- "Change language to Tamil."
- "Can you speak in Malayalam?"

### 6. Recipient and Payment Help

- "I want to pay someone new."
- "How can I add a recipient?"
- "I want to send money to a mobile number."
- "How do I confirm a payment?"

### Example Conversation

**You:** Send ₹500 to Amma.

**BolPay:** Please enter your demo PIN to confirm the payment.

**You:** Enters the demo PIN.

**BolPay:** Your demo payment of ₹500 to Amma was successful!

*Note: These are example commands. The available recipients depend on the recipients configured in the application. All payments are simulated in Demo Mode and no real money is transferred.*

## Security and Privacy

- Never commit API keys, credentials, or `.env` files to a public repository.
- Payment PIN verification is handled on the frontend.
- Do not share personal banking credentials or real UPI PINs.

## Future Improvements

- Integration with authorised payment providers for real UPI payments.
- Improved voice recognition and response speed.
- Accessibility improvements for senior citizens.
- Enhanced security and authentication.
- Wider language and regional support.

## Project Goal

BoloPay aims to make digital payments simpler, more accessible, and easier to understand through natural voice interaction.
####
*All payments are simulated in Demo Mode and no real money is transferred.*
