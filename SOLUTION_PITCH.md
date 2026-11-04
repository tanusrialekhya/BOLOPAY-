<h1 align="center">BOLPAY💙</h1>

<p align="center"><b>Voice-First Payment Assistant</b></p>

<p align="center">
Built solo for the Great Indian AI Internship Challenge 2026 by Gnani.ai
</p>

<p align="center">
🔗 <a href="https://bolpay.streamlit.app/">Live demo</a> &nbsp;|&nbsp;
🎥 <a href="https://x.com/tanusri_alekhya/status/2117014165307146609">Demo video</a> &nbsp;|&nbsp;
💻 <a href="https://github.com/tanusrialekhya/BOLPAY-">GitHub</a>
</p>

---

## Problem
- Payment apps use small text, many screens and English-heavy menus.
- Senior citizens and first-time smartphone users find them hard to use.
- Many avoid digital payments or depend on others to send money.

## Solution
- Pay by speaking in your own language, for example "Pay 500 rupees to Amma".
- BOLPAY understands the request, asks for a PIN, completes the payment and speaks the result.
- Also supports balance checks, transaction history, app help and language switching by voice.
- Works in 10 Indian languages: English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati and Punjabi.

## Gnani models used
- **Gnani Prisma v2.5:** speech-to-text
- **Gnani Timbre v2.5:** text-to-speech
- **GPT-OSS-20B (via Groq):** understands what the user wants

## What I built (solo)
- Browser voice component with voice activity detection that streams audio over WebSocket
- FastAPI backend that manages voice sessions and calls the speech and language models
- Intent handling for pay, balance, history, language change and help
- Payment flow with recipient selection, PIN confirmation and wallet balance
- Multilingual screens and prompts for all 10 languages
- Separate deployment of the Streamlit frontend and the backend

## Skills used
- Python, FastAPI, async programming
- WebSockets and real-time audio streaming
- JavaScript and browser microphone handling
- Streamlit
- Speech, language and text-to-speech APIs
- Conversational flow and intent design
- Multilingual (i18n) design
- Accessibility-focused UX
- Cloud deployment, secrets management and debugging

## Demo mode and limitations
- All payments are simulated; no real money moves.
- PIN check runs in the frontend (demo only); production needs server-side verification.
- Accuracy depends on audio quality and network speed.

## Next steps
- Server-side authentication
- Real UPI payments through authorised providers
- Faster responses and more dialects
