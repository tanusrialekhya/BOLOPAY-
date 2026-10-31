"""BoloPay backend:  uvicorn backend:app --port 8000

audio -> Gnani STT only -> Groq gpt-oss-20b -> Gnani TTS only

The language never changes unless the user picks it (dropdown) or clearly says "change language to ...".

.env: GROQ_API_KEY, GNANI_STT_API_KEY, GNANI_TTS_API_KEY

This server never moves money and never accepts a PIN."""

import os, json, base64, asyncio, tempfile, threading

from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from datetime import datetime, timezone

from pathlib import Path

import re

import unicodedata
import math

BALANCE_PATTERNS = {

    "en-IN": [

        r"\bwhat is my balance\b",

        r"\bmy balance\b",

        r"\bcheck my balance\b",

        r"\bhow much money do i have\b",

        r"\bhow much balance\b",

    ],

    "hi-IN": [

        "मेरा बैलेंस",

        "मेरा बैलेंस कितना है",

        "मेरे खाते में कितने पैसे",

        "बैलेंस चेक करो",

    ],

    "te-IN": [

        "నా బ్యాలెన్స్",

        "నా బ్యాలెన్స్ ఎంత",

        "నా అకౌంట్ లో ఎంత",

        "బ్యాలెన్స్ ఎంత",

    ],

    "ta-IN": [

        "என் பேலன்ஸ்",

        "என் கணக்கில் எவ்வளவு பணம்",

        "என் பேலன்ஸ் எவ்வளவு",

    ],

    "kn-IN": [

        "ನನ್ನ ಬ್ಯಾಲೆನ್ಸ್",

        "ನನ್ನ ಖಾತೆಯಲ್ಲಿ ಎಷ್ಟು ಹಣ",

        "ಬ್ಯಾಲೆನ್ಸ್ ಎಷ್ಟು",

    ],

    "ml-IN": [

        "എന്റെ ബാലൻസ്",

        "എന്റെ അക്കൗണ്ടിൽ എത്ര പണം",

        "ബാലൻസ് എത്ര",

    ],

    "bn-IN": [

        "আমার ব্যালেন্স",

        "আমার অ্যাকাউন্টে কত টাকা",

        "ব্যালেন্স কত",

    ],

    "mr-IN": [

        "माझा बॅलन्स",

        "माझ्या खात्यात किती पैसे",

        "बॅलन्स किती",

    ],

    "gu-IN": [

        "મારું બેલેન્સ",

        "મારા ખાતામાં કેટલા પૈસા",

        "બેલેન્સ કેટલું",

    ],

    "pa-IN": [

        "ਮੇਰਾ ਬੈਲੰਸ",

        "ਮੇਰੇ ਖਾਤੇ ਵਿੱਚ ਕਿੰਨੇ ਪੈਸੇ",

        "ਬੈਲੰਸ ਕਿੰਨਾ",

    ],

}

BALANCE_UNAVAILABLE = {
    "en-IN": "Sorry, I can't retrieve your balance right now.",
    "hi-IN": "क्षमा कीजिए, मैं अभी आपका बैलेंस नहीं बता पा रहा हूँ।",
    "te-IN": "క్షమించండి, ప్రస్తుతం మీ బ్యాలెన్స్‌ను తెలుసుకోలేకపోతున్నాను.",
    "ta-IN": "மன்னிக்கவும், இப்போது உங்கள் இருப்புத் தொகையைப் பெற முடியவில்லை.",
    "kn-IN": "ಕ್ಷಮಿಸಿ, ಈಗ ನಿಮ್ಮ ಖಾತೆಯ ಬಾಕಿಯನ್ನು ಪಡೆಯಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ.",
    "ml-IN": "ക്ഷമിക്കണം, ഇപ്പോൾ നിങ്ങളുടെ ബാലൻസ് ലഭ്യമാക്കാൻ കഴിയുന്നില്ല.",
    "bn-IN": "দুঃখিত, এই মুহূর্তে আপনার ব্যালেন্স জানা যাচ্ছে না।",
    "mr-IN": "क्षमस्व, सध्या तुमची शिल्लक मिळवता येत नाही.",
    "gu-IN": "માફ કરશો, અત્યારે તમારું બેલેન્સ મેળવી શકાતું નથી.",
    "pa-IN": "ਮਾਫ਼ ਕਰਨਾ, ਇਸ ਵੇਲੇ ਤੁਹਾਡਾ ਬਕਾਇਆ ਨਹੀਂ ਮਿਲ ਸਕਦਾ।",
}

BALANCE_REPLY = {
    "en-IN": "Your current balance is ₹{amount:,.2f}.",
    "hi-IN": "आपका मौजूदा बैलेंस ₹{amount:,.2f} है।",
    "te-IN": "మీ ప్రస్తుత బ్యాలెన్స్ ₹{amount:,.2f}.",
    "ta-IN": "உங்கள் தற்போதைய இருப்புத் தொகை ₹{amount:,.2f}.",
    "kn-IN": "ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಖಾತೆಯ ಬಾಕಿ ₹{amount:,.2f}.",
    "ml-IN": "നിങ്ങളുടെ നിലവിലെ ബാലൻസ് ₹{amount:,.2f} ആണ്.",
    "bn-IN": "আপনার বর্তমান ব্যালেন্স ₹{amount:,.2f}।",
    "mr-IN": "तुमची सध्याची शिल्लक ₹{amount:,.2f} आहे.",
    "gu-IN": "તમારું હાલનું બેલેન્સ ₹{amount:,.2f} છે.",
    "pa-IN": "ਤੁਹਾਡਾ ਮੌਜੂਦਾ ਬਕਾਇਆ ₹{amount:,.2f} ਹੈ।",
}
def normalize_text(text: str) -> str:

    text = unicodedata.normalize("NFC", text or "")

    return re.sub(r"\s+", " ", text.strip().lower())

def is_balance_question(text: str, lang: str) -> bool:

    text = normalize_text(text)

    patterns = BALANCE_PATTERNS.get(lang, [])

    return any(

        re.search(pattern, text) if lang == "en-IN"

        else pattern in text

        for pattern in patterns

    )

load_dotenv()

GNANI_STT_KEY = os.getenv("GNANI_STT_API_KEY", "")

GNANI_TTS_KEY = os.getenv("GNANI_TTS_API_KEY", "")

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

ok_key = lambda k: bool(k) and "paste_your" not in k

HAVE_GNANI, HAVE_GROQ, HAVE_TTS = ok_key(GNANI_STT_KEY), ok_key(GROQ_KEY), ok_key(GNANI_TTS_KEY)

LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")

GNANI_TTS_MODEL = os.getenv("GNANI_TTS_MODEL", "timbre-v2.5")

LIVE_TTS = os.getenv("LIVE_TTS", "1") != "0"

STREAM_RATE = 16000

_env_voice = os.getenv("GNANI_VOICE", "").strip()

VOICE_CANDIDATES = ([_env_voice] if _env_voice else []) + [None, "Nalini", "Kaveri", "Shubhra"]

app = FastAPI()

CONTACTS = ["Amma", "Dad", "Rahul", "Priya", "Shopkeeper"]

LANGS = ["en-IN", "hi-IN", "te-IN", "ta-IN", "kn-IN", "ml-IN", "bn-IN", "mr-IN", "gu-IN", "pa-IN"]

SCREENS = ["home", "history", "balance", "scan", "help", "pay"]

FONTS = ["Small", "Medium", "Large"]

CANNED = {

    "en-IN": "Sorry, I didn't catch that. Please tap and say it again.",

    "hi-IN": "माफ़ कीजिए, सुनाई नहीं दिया। कृपया फिर से बोलें।",

    "te-IN": "క్షమించండి, వినిపించలేదు. దయచేసి మళ్లీ చెప్పండి.",

    "ta-IN": "மன்னிக்கவும், கேட்கவில்லை. மீண்டும் சொல்லுங்கள்.",

    "kn-IN": "ಕ್ಷಮಿಸಿ, ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಹೇಳಿ.",

    "ml-IN": "ക്ഷമിക്കണം, കേട്ടില്ല. ദയവായി വീണ്ടും പറയൂ.",

    "bn-IN": "দুঃখিত, শুনতে পাইনি। অনুগ্রহ করে আবার বলুন।",

    "mr-IN": "माफ करा, ऐकू आले नाही. कृपया पुन्हा बोला.",

    "gu-IN": "માફ કરશો, સંભળાયું નહીં. કૃપા કરીને ફરી બોલો.",

    "pa-IN": "ਮਾਫ਼ ਕਰਨਾ, ਸੁਣਾਈ ਨਹੀਂ ਦਿੱਤਾ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ।",

}

OUT_OF_SCOPE = {
    "en-IN": "I don't know that. I can help with BoloPay payments, balance, history, and QR scanning.",
    "hi-IN": "मुझे इसकी जानकारी नहीं है। मैं BoloPay भुगतान, बैलेंस, हिस्ट्री और QR स्कैन में मदद कर सकता हूँ।",
    "te-IN": "దాని గురించి నాకు తెలియదు. BoloPay చెల్లింపులు, బ్యాలెన్స్, చరిత్ర, QR స్కానింగ్‌లో సహాయం చేయగలను.",
    "ta-IN": "அது எனக்குத் தெரியாது. BoloPay பணப்பரிவர்த்தனை, இருப்பு, வரலாறு, QR ஸ்கேன் ஆகியவற்றில் உதவ முடியும்.",
    "kn-IN": "ಅದರ ಬಗ್ಗೆ ನನಗೆ ತಿಳಿದಿಲ್ಲ. BoloPay ಪಾವತಿ, ಬಾಕಿ, ಇತಿಹಾಸ ಮತ್ತು QR ಸ್ಕ್ಯಾನ್‌ನಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಹುದು.",
    "ml-IN": "അത് എനിക്ക് അറിയില്ല. BoloPay പേയ്‌മെന്റ്, ബാലൻസ്, ഇടപാട് ചരിത്രം, QR സ്കാൻ എന്നിവയിൽ സഹായിക്കാം.",
    "bn-IN": "এটি আমার জানা নেই। BoloPay পেমেন্ট, ব্যালেন্স, ইতিহাস ও QR স্ক্যানে সাহায্য করতে পারি।",
    "mr-IN": "मला त्याची माहिती नाही. मी BoloPay पेमेंट, शिल्लक, व्यवहार इतिहास आणि QR स्कॅनमध्ये मदत करू शकतो.",
    "gu-IN": "મને તેની જાણ નથી. હું BoloPay પેમેન્ટ, બેલેન્સ, ઇતિહાસ અને QR સ્કેનમાં મદદ કરી શકું છું.",
    "pa-IN": "ਮੈਨੂੰ ਇਸ ਬਾਰੇ ਪਤਾ ਨਹੀਂ। ਮੈਂ BoloPay ਭੁਗਤਾਨ, ਬਕਾਇਆ, ਇਤਿਹਾਸ ਅਤੇ QR ਸਕੈਨ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ।",
}

SERVICE_ERROR = {
    "en-IN": "Sorry, the assistant is temporarily unavailable. Please try again in a moment.",
    "hi-IN": "क्षमा कीजिए, सहायक अभी उपलब्ध नहीं है। कृपया थोड़ी देर बाद फिर कोशिश करें।",
    "te-IN": "క్షమించండి, సహాయకుడు తాత్కాలికంగా అందుబాటులో లేరు. కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి.",
    "ta-IN": "மன்னிக்கவும், உதவியாளர் தற்காலிகமாக கிடைக்கவில்லை. சிறிது நேரம் கழித்து முயற்சிக்கவும்.",
    "kn-IN": "ಕ್ಷಮಿಸಿ, ಸಹಾಯಕರು ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    "ml-IN": "ക്ഷമിക്കണം, സഹായി താൽക്കാലികമായി ലഭ്യമല്ല. കുറച്ച് കഴിഞ്ഞ് വീണ്ടും ശ്രമിക്കുക.",
    "bn-IN": "দুঃখিত, সহায়কটি সাময়িকভাবে উপলব্ধ নয়। একটু পরে আবার চেষ্টা করুন।",
    "mr-IN": "क्षमस्व, सहाय्यक सध्या उपलब्ध नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
    "gu-IN": "માફ કરશો, સહાયક અત્યારે ઉપલબ્ધ નથી. થોડી વાર પછી ફરી પ્રયાસ કરો.",
    "pa-IN": "ਮਾਫ਼ ਕਰਨਾ, ਸਹਾਇਕ ਇਸ ਵੇਲੇ ਉਪਲਬਧ ਨਹੀਂ। ਕੁਝ ਦੇਰ ਬਾਅਦ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
}

BALANCE_OPEN = {
    "en-IN": "Opening your balance. Please enter your PIN on the screen.",
    "hi-IN": "बैलेंस खोल रहा हूँ। कृपया स्क्रीन पर अपना पिन दर्ज करें।",
    "te-IN": "మీ బ్యాలెన్స్ తెరుస్తున్నాను. దయచేసి స్క్రీన్‌పై మీ పిన్ నమోదు చేయండి.",
    "ta-IN": "உங்கள் இருப்புத் தொகையைத் திறக்கிறேன். திரையில் உங்கள் பின்னை உள்ளிடவும்.",
    "kn-IN": "ನಿಮ್ಮ ಬಾಕಿಯನ್ನು ತೆರೆಯುತ್ತಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಪರದೆಯಲ್ಲಿ ನಿಮ್ಮ ಪಿನ್ ನಮೂದಿಸಿ.",
    "ml-IN": "നിങ്ങളുടെ ബാലൻസ് തുറക്കുന്നു. സ്ക്രീനിൽ പിൻ നൽകുക.",
    "bn-IN": "ব্যালেন্স খুলছি। অনুগ্রহ করে স্ক্রিনে আপনার পিন দিন।",
    "mr-IN": "बॅलन्स उघडत आहे. कृपया स्क्रीनवर तुमचा पिन टाका.",
    "gu-IN": "બેલેન્સ ખોલી રહ્યો છું. કૃપા કરીને સ્ક્રીન પર તમારો પિન દાખલ કરો.",
    "pa-IN": "ਬਕਾਇਆ ਖੋਲ੍ਹ ਰਿਹਾ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਸਕ੍ਰੀਨ ਉੱਤੇ ਆਪਣਾ ਪਿੰਨ ਦਰਜ ਕਰੋ।",
}

PAY_READY = {
    "en-IN": "Opening payments. Please enter your PIN on the screen.",
    "hi-IN": "पेमेंट खोल रहा हूँ। कृपया स्क्रीन पर अपना पिन दर्ज करें।",
    "te-IN": "పేమెంట్స్ తెరుస్తున్నాను. దయచేసి స్క్రీన్‌పై మీ పిన్ నమోదు చేయండి.",
    "ta-IN": "பேமெண்ட் திரையைத் திறக்கிறேன். திரையில் உங்கள் பின்னை உள்ளிடவும்.",
    "kn-IN": "ಪಾವತಿ ತೆರೆಯುತ್ತಿದೆ. ದಯವಿಟ್ಟು ಪರದೆಯಲ್ಲಿ ನಿಮ್ಮ ಪಿನ್ ನಮೂದಿಸಿ.",
    "ml-IN": "പേയ്‌മെന്റ് തുറക്കുന്നു. സ്ക്രീനിൽ നിങ്ങളുടെ പിൻ നൽകുക.",
    "bn-IN": "পেমেন্ট খুলছি। অনুগ্রহ করে স্ক্রিনে আপনার পিন দিন।",
    "mr-IN": "पेमेंट उघडत आहे. कृपया स्क्रीनवर तुमचा पिन टाका.",
    "gu-IN": "પેમેન્ટ ખોલી રહ્યો છું. કૃપા કરીને સ્ક્રીન પર તમારો પિન દાખલ કરો.",
    "pa-IN": "ਪੇਮੈਂਟ ਖੋਲ੍ਹ ਰਿਹਾ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਸਕ੍ਰੀਨ ਉੱਤੇ ਆਪਣਾ ਪਿੰਨ ਦਰਜ ਕਰੋ।",
}

HELLO = {

    "en-IN": "Hello! How can I help you?",

    "hi-IN": "नमस्ते! मैं आपकी कैसे मदद करूँ?",

    "te-IN": "నమస్కారం! నేను మీకు ఎలా సహాయం చేయగలను?",

    "ta-IN": "வணக்கம்! நான் எப்படி உதவலாம்?",

    "kn-IN": "ನಮಸ್ಕಾರ! ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",

    "ml-IN": "നമസ്കാരം! ഞാൻ എങ്ങനെ സഹായിക്കണം?",

    "bn-IN": "নমস্কার! আমি কীভাবে সাহায্য করতে পারি?",

    "mr-IN": "नमस्कार! मी तुम्हाला कशी मदत करू?",

    "gu-IN": "નમસ્તે! હું તમને કેવી રીતે મદદ કરી શકું?",

    "pa-IN": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰਾਂ?",

}

# words that must appear in what the user said before a language change is accepted

LANG_WORDS = ["language", "भाषा", "భాష", "மொழி", "ಭಾಷೆ", "ഭാഷ", "ভাষা", "ભાષા", "ਭਾਸ਼ਾ",

              "english", "hindi", "telugu", "tamil", "kannada", "malayalam", "bengali", "marathi", "gujarati", "punjabi",

              "हिंदी", "हिन्दी", "తెలుగు", "தமிழ்", "ಕನ್ನಡ", "മലയാളം", "বাংলা", "मराठी", "ગુજરાતી", "ਪੰਜਾਬੀ", "अंग्रेज़ी", "अंग्रेजी"]

try:

    with open(os.path.join("knowledge", "bolopay_knowledge.txt"), encoding="utf-8") as f:

        KNOWLEDGE = f.read()

except Exception:

    KNOWLEDGE = ""

SYSTEM = f"""You are BoloPay, a friendly voice payment assistant (DEMO: no real money moves).

Reply with ONLY one JSON object:

{{

    "category": "PAYMENT_QA | NAVIGATION | OUT_OF_SCOPE | UNCLEAR",

    "supported": true,

    "said": "...",

    "reply": "...",

    "actions": []

}}

INPUT: app_state.heard_options = the SAME audio transcribed by 1-2 speech engines. They can contain mistakes

(wrong words, numbers, names). Combine them and use common sense. Fix mis-heard contact names, numbers and amounts.

"said" = the sentence the user most likely said, corrected, in the same language and native script.

The user speaks the language app_state.language. "reply" is ONE short sentence, written ONLY in that

language's native script. NEVER answer in any other language.

TOOLS (zero or more in "actions"):

 {{"tool":"open_screen","screen":"home|history|balance|scan|help|pay","mode":"camera|gallery"}}   (mode only for scan)

 {{"tool":"prepare_payment","payee":"\<contact in English OR 10-digit mobile>","amount":\<number>}}

 {{"tool":"set_language","lang":"\<code from {LANGS}>"}}   ONLY if the user clearly asked to change the language

 {{"tool":"set_font","size":"Small|Medium|Large"}}

 {{"tool":"cancel"}}

 OUTPUT FORMAT:

Return ONLY one valid JSON object with these fields:

{{

    "category": "PAYMENT_QA",

    "supported": true,

    "said": "User's recognized question",

    "reply": "Assistant response in the user's language",

    "actions": []

}}

Allowed categories:

\- PAYMENT_QA: Questions about BoloPay payment information.about what bolopay mean what it does how many languages it can speak.

\- NAVIGATION: Requests to open or navigate website features.

\- OUT_OF_SCOPE: Questions unrelated to BoloPay.

\- UNCLEAR: Questions whose intent cannot be determined.

For unsupported information, set supported to false.

Never answer unrelated general-knowledge questions.

Preserve the user's language in every response.

CONTACTS: {", ".join(CONTACTS)}. Amma=mother/mummy/maa/అమ్మ/अम्मा/அம்மா/ಅಮ್ಮ/അമ്മ, Dad=father/papa/నాన్న/पापा/அப்பா/ಅಪ್ಪ/അച്ഛൻ,

Shopkeeper=dukaan/dukandar. Convert spoken numbers to digits ("five hundred"/"ఐదు వందలు"/"पाँच सौ" -> 500).

RULES: "Pay 500 to Rahul" -> prepare_payment. The payee may be a saved contact (Amma, Dad, Rahul, Priya, Shopkeeper), OR any person's name exactly as the user said it, OR a valid 10-digit Indian mobile number. Never refuse a payment because the name is not a saved contact. The app opens its existing payments/PIN screen after preparation. Speak the payment-ready message once; do not interrupt while the user is entering the PIN. The PIN is entered only in the frontend and is never sent to this backend. "Open camera / scan" -> open_screen scan camera.

Balance, history, help, home and font requests are normal: do them. If amount or payee is missing, no action, say which is

missing. If the audio is meaningless, no action and ask them to repeat. Never ask the user to speak a PIN, and never accept or store a PIN in this backend.

This is a competition demo: payments are simulated only. Never imply real money moved. A payment is successful only after the user confirms the demo payment and the backend records it. No chit-chat, no questions.

{("HELP INFO:" + chr(10) + KNOWLEDGE) if KNOWLEDGE else ""}"""

# ---------------------------------------------------------------- demo wallet (SIMULATION ONLY)
DEMO_STORE_FILE = Path(__file__).resolve().parent / "demo_wallet.json"
DEMO_STARTING_BALANCE = 5000.00
DEMO_MAX_AMOUNT = 100000.00

def _load_demo_store():
    try:
        data = json.loads(DEMO_STORE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def _save_demo_store(data):
    temp = DEMO_STORE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(DEMO_STORE_FILE)

def _demo_user_key(user_id):
    # Demo-only identifier; real authentication is outside this competition prototype.
    value = re.sub(r"[^A-Za-z0-9_-]", "", str(user_id or "demo-user"))[:64]
    return value or "demo-user"

def get_demo_wallet(user_id="demo-user"):
    data = _load_demo_store()
    key = _demo_user_key(user_id)
    wallet = data.get(key)
    if not isinstance(wallet, dict):
        wallet = {"balance": DEMO_STARTING_BALANCE, "transactions": []}
        data[key] = wallet
        _save_demo_store(data)
    wallet.setdefault("balance", DEMO_STARTING_BALANCE)
    wallet.setdefault("transactions", [])
    return wallet

def complete_demo_payment(user_id, payee, amount):
    amount = float(amount)
    if not math.isfinite(amount):
        raise ValueError("Invalid demo payment amount")
    amount = round(amount, 2)
    payee = str(payee or "").strip()
    valid_contact = any(payee.lower() == name.lower() for name in CONTACTS)
    valid_phone = norm_phone(payee)
    if not (valid_contact or valid_phone) or not (0 < amount <= DEMO_MAX_AMOUNT):
        raise ValueError("Invalid demo payment details")
    payee = valid_phone or next(name for name in CONTACTS if payee.lower() == name.lower()) if valid_contact else valid_phone
    data = _load_demo_store()
    key = _demo_user_key(user_id)
    wallet = data.get(key) or {"balance": DEMO_STARTING_BALANCE, "transactions": []}
    balance = round(float(wallet.get("balance", DEMO_STARTING_BALANCE)), 2)
    if amount > balance:
        return {"success": False, "reason": "insufficient_demo_balance", "balance": balance}
    tx = {
        "id": "DEMO-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
        "payee": str(payee)[:80],
        "amount": amount,
        "status": "SUCCESS",
        "mode": "SIMULATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    wallet["balance"] = round(balance - amount, 2)
    wallet["transactions"] = [tx] + list(wallet.get("transactions", []))[:99]
    data[key] = wallet
    _save_demo_store(data)
    return {"success": True, "transaction": tx, "balance": wallet["balance"], "mode": "SIMULATED"}

# ---------------------------------------------------------------- helpers

def norm_phone(s):

    d = re.sub(r"\D", "", str(s))

    if len(d) == 12 and d.startswith("91"):

        d = d[2:]

    elif len(d) == 11 and d.startswith("0"):

        d = d[1:]

    return d if re.fullmatch(r"[6-9]\d{9}", d) else None

def canned(lang):

    return CANNED.get(lang, CANNED["en-IN"])

def clean_actions(raw, heard_text):

    out, bad_pay = [], False

    if not isinstance(raw, list):

        return out, bad_pay

    asked_lang = any(w in heard_text.lower() for w in LANG_WORDS)

    for a in raw[:4]:

        if not isinstance(a, dict):

            continue

        t = a.get("tool")

        if t == "open_screen" and a.get("screen") in SCREENS:

            o = {"tool": t, "screen": a["screen"]}

            if a["screen"] == "scan" and a.get("mode") in ("camera", "gallery"):

                o["mode"] = a["mode"]

            out.append(o)

        elif t == "prepare_payment":
            payee = re.sub(r"\s+", " ", str(a.get("payee", ""))).strip()[:40]
            phone = norm_phone(payee)
            contact = next((c for c in CONTACTS if c.lower() == payee.lower()), None)
            try:
                amount = round(float(a.get("amount")), 2)
            except (TypeError, ValueError):
                amount = 0
            has_name = bool(payee) and any(ch.isalpha() for ch in payee)
            if (phone or contact or has_name) and 0 < amount <= 100000:
                return [{"tool": "prepare_payment", "payee": phone or contact or payee, "amount": amount}], False
            bad_pay = True

        elif t == "set_language" and a.get("lang") in LANGS and asked_lang:      # never on its own

            out.append({"tool": t, "lang": a["lang"]})

        elif t == "set_font" and a.get("size") in FONTS:

            out.append({"tool": t, "size": a["size"]})

        elif t == "cancel":

            out.append({"tool": t})

    return out, bad_pay

_RANGES = {"hi-IN": [(0x0900, 0x097F)], "mr-IN": [(0x0900, 0x097F)], "bn-IN": [(0x0980, 0x09FF)],

           "pa-IN": [(0x0A00, 0x0A7F)], "gu-IN": [(0x0A80, 0x0AFF)], "ta-IN": [(0x0B80, 0x0BFF)],

           "te-IN": [(0x0C00, 0x0C7F)], "kn-IN": [(0x0C80, 0x0CFF)], "ml-IN": [(0x0D00, 0x0D7F)]}

def script_ok(text, lang):

    letters = [c for c in text if c.isalpha()]

    if not letters:

        return True

    if lang == "en-IN":

        return sum(1 for c in letters if c.isascii()) / len(letters) >= 0.8

    rng = _RANGES.get(lang)

    if not rng:

        return True

    return sum(1 for c in letters if any(lo <= ord(c) <= hi for lo, hi in rng)) / len(letters) >= 0.6

PAY_RE = re.compile(r"(?:pay|send)\s+(?:rs\.?\s*|₹\s*)?(\d[\d,]*)\s*(?:rupees|rs)?\s+to\s+([\w\s+-]+)", re.I)

def rule_based(text):

    """Offline English fallback if the LLM is unreachable."""

    m = PAY_RE.search(text)

    if m:

        return {"reply": PAY_READY["en-IN"],

                "actions": [{"tool": "prepare_payment", "payee": m.group(2).strip(),

                             "amount": float(m.group(1).replace(",", ""))}]}

    t = text.lower()

    if "cancel" in t:

        return {"reply": "Cancelled.", "actions": [{"tool": "cancel"}]}

    if "camera" in t:

        return {"reply": "Opening camera.", "actions": [{"tool": "open_screen", "screen": "scan", "mode": "camera"}]}

    for word, screen in (("balance", "balance"), ("history", "history"), ("transaction", "history"),

                         ("scan", "scan"), ("help", "help"), ("home", "home")):

        if word in t:

            return {"reply": f"Opening {screen}.", "actions": [{"tool": "open_screen", "screen": screen}]}

    return None

# ---------------------------------------------------------------- STT (Gnani only; selected app language)

EN_PROMPT = ("BoloPay voice payment. Pay 500 rupees to Amma. Send 200 to Dad, Rahul, Priya or Shopkeeper. "

             "Show balance, history, scan QR, open camera.")

def _extract(r):

    if r is None:

        return ""

    if isinstance(r, str):

        return r.strip()

    get = (lambda k: r.get(k)) if isinstance(r, dict) else (lambda k: getattr(r, k, None))

    for k in ("transcript", "full_transcript", "text"):

        v = get(k)

        if isinstance(v, str) and v.strip():

            return v.strip()

        if isinstance(v, dict):

            t = _extract(v)

            if t:

                return t

    files = get("files")

    if files:

        return _extract(files[0] if not isinstance(files, dict) else list(files.values())[0])

    return ""

def _gnani_stt(wav, lang):

    fd, path = tempfile.mkstemp(suffix=".wav", prefix="bolopay_")

    try:

        with os.fdopen(fd, "wb") as f:

            f.write(wav)

        try:

            from gnani.stt import GnaniSTTClient

            r = GnaniSTTClient(api_key=GNANI_STT_KEY).transcribe(path, language_code=lang)

        except ImportError:

            from gnani.stt import GnaniSTTBatchClient

            r = GnaniSTTBatchClient(api_key=GNANI_STT_KEY).transcribe(files=path, language_code=lang)

    finally:

        try:

            os.remove(path)

        except OSError:

            pass

    return _extract(r)

async def hear(wav, lang):
    """Transcribe with Gnani STT only, using the selected app language."""
    if not HAVE_GNANI:
        raise RuntimeError("GNANI_STT_API_KEY is missing or invalid.")
    try:
        transcript = await asyncio.wait_for(
            asyncio.to_thread(_gnani_stt, wav, lang), timeout=25
        )
    except Exception:
        raise RuntimeError("The speech service is busy. Please try again.") from None
    transcript = transcript.strip() if isinstance(transcript, str) else ""
    if transcript and script_ok(transcript, lang):
        return [transcript]
    return []

# ---------------------------------------------------------------- LLM (gpt-oss on Groq)

_GROQ_A = None

_LLM_OPTIONS = {"extra_body": {"reasoning_effort": "low"}, "response_format": {"type": "json_object"}}

def groq_async():

    global _GROQ_A

    if _GROQ_A is None:

        from groq import AsyncGroq

        _GROQ_A = AsyncGroq(api_key=GROQ_KEY, max_retries=0, timeout=9.0)

    return _GROQ_A

async def llm(ctx):
    """One bounded GPT-OSS request. Parse the JSON directly; never regex-match it."""
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps({"app_state": ctx}, ensure_ascii=False)},
    ]
    response = await asyncio.wait_for(
        groq_async().chat.completions.create(
            model=LLM_MODEL,
            messages=msgs,
            temperature=0.1,
            max_tokens=500,
            **_LLM_OPTIONS,
        ),
        timeout=10,
    )
    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("Groq returned an empty response")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Defensive extraction if the provider adds surrounding text despite JSON mode.
        left, right = content.find("{"), content.rfind("}")
        if left < 0 or right <= left:
            raise RuntimeError("Groq returned invalid JSON")
        data = json.loads(content[left:right + 1])
    if not isinstance(data, dict):
        raise RuntimeError("Groq response was not a JSON object")
    return data

async def understand(cands, lang, msg):

    heard_text = " ".join(cands)

    ctx = {"language": lang, "heard_options": cands, "screen": msg.get("screen"),

           "last_payee": msg.get("payee"), "last_amount": msg.get("amount"),

           "recent": (msg.get("history") or [])[-3:]}

    try:

        data = await llm(ctx)

    except Exception as e:
        data = None
        # Keep essential navigation/payment commands usable if Groq is temporarily down.
        if lang == "en-IN":
            for candidate in cands:
                data = rule_based(candidate)
                if data:
                    break
        data = data or {"category": "SERVICE_ERROR", "supported": False,
                        "reply": SERVICE_ERROR.get(lang, SERVICE_ERROR["en-IN"]), "actions": []}

    actions, bad_pay = clean_actions(data.get("actions"), heard_text)

    out_lang, switched = lang, False

    for a in actions:

        if a["tool"] == "set_language":

            out_lang, switched = a["lang"], True

    said = str(data.get("said") or "").strip()

    if not said or not script_ok(said, lang):

        said = cands[0]

    reply = str(data.get("reply") or "").strip()

    if str(data.get("category", "")).upper() == "OUT_OF_SCOPE" or data.get("supported") is False:
        reply = OUT_OF_SCOPE.get(out_lang, OUT_OF_SCOPE["en-IN"])
        actions = []

    if actions and actions[0]["tool"] == "prepare_payment":

        reply = PAY_READY.get(out_lang, PAY_READY["en-IN"])

    elif switched:

        reply = HELLO.get(out_lang, HELLO["en-IN"])

    elif bad_pay or not reply or not script_ok(reply, out_lang):
        reply = SERVICE_ERROR.get(out_lang, SERVICE_ERROR["en-IN"])

    return said, reply, out_lang, actions

# ---------------------------------------------------------------- TTS

_TTS_LOCK = asyncio.Lock()

_VOICE_OK = {}

_AUDIO = {}

def _voices(lang):

    v = VOICE_CANDIDATES[:]

    if lang in _VOICE_OK and _VOICE_OK[lang] in v:

        v.remove(_VOICE_OK[lang])

        v.insert(0, _VOICE_OK[lang])

    return v

def _stream_worker(text, lang, voice, loop, q):

    try:

        from gnani.tts import GnaniTTSStreamClient, AudioConfig

        kw = dict(model=GNANI_TTS_MODEL, language=lang,

                  audio_config=AudioConfig(sample_rate=STREAM_RATE, encoding="linear_pcm", container="raw"))

        if voice:

            kw["voice"] = voice

        first = True

        for chunk in GnaniTTSStreamClient(api_key=GNANI_TTS_KEY).synthesize_stream(text, **kw):

            if not chunk:

                continue

            if first and chunk[:4] == b"RIFF":

                chunk = chunk[44:] if len(chunk) > 44 else b""

            first = False

            if chunk:

                loop.call_soon_threadsafe(q.put_nowait, chunk)

        loop.call_soon_threadsafe(q.put_nowait, None)

    except Exception as e:

        loop.call_soon_threadsafe(q.put_nowait, e)

async def stream_audio(ws, text, lang):

    if not (LIVE_TTS and text and HAVE_TTS):

        return False

    key = (text, lang)

    if key in _AUDIO:

        await ws.send_json({"type": "audio_start", "format": "pcm16", "rate": STREAM_RATE})

        for c in _AUDIO[key]:

            await ws.send_bytes(c)

        return True

    loop = asyncio.get_running_loop()

    async with _TTS_LOCK:

        for voice in _voices(lang):

            q, buf = asyncio.Queue(), []

            threading.Thread(target=_stream_worker, args=(text, lang, voice, loop, q), daemon=True).start()

            while True:

                item = await q.get()

                if item is None:

                    if buf:

                        _VOICE_OK[lang] = voice

                        if len(_AUDIO) < 80:

                            _AUDIO[key] = buf


                        return True

                    break

                if isinstance(item, Exception):


                    if buf:

                        return True

                    break

                if not buf:

                    await ws.send_json({"type": "audio_start", "format": "pcm16", "rate": STREAM_RATE})

                buf.append(item)

                await ws.send_bytes(item)

    return False

def _tts_sync(text, lang, voice):

    from gnani.tts import GnaniTTSClient, AudioConfig

    kw = dict(model=GNANI_TTS_MODEL, language=lang,

              audio_config=AudioConfig(sample_rate=16000, encoding="linear_pcm", container="wav"))

    if voice:

        kw["voice"] = voice

    r = GnaniTTSClient(api_key=GNANI_TTS_KEY).synthesize(text, **kw)

    if isinstance(r, (bytes, bytearray)):

        return bytes(r)

    for k in ("audio", "audio_content", "content", "data"):

        v = r.get(k) if isinstance(r, dict) else getattr(r, k, None)

        if isinstance(v, (bytes, bytearray)):

            return bytes(v)

    raise RuntimeError("Gnani TTS returned no audio bytes")

async def clip_audio(text, lang):
    """Synthesize with Gnani TTS only; never use a third-party fallback."""
    if not HAVE_TTS:
        return None
    async with _TTS_LOCK:
        for voice in _voices(lang):
            try:
                audio = await asyncio.to_thread(_tts_sync, text, lang, voice)
                if audio:
                    _VOICE_OK[lang] = voice
                    return audio
            except Exception:
                continue
    return None

async def speak_out(ws, text, lang):

    lang = lang if lang in LANGS else "en-IN"

    if not await stream_audio(ws, text, lang):

        audio = await clip_audio(text, lang)

        if audio:

            await ws.send_bytes(audio)

    await ws.send_json({"type": "done"})

# ---------------------------------------------------------------- one request

async def handle(ws, msg):

    lang = msg.get("language") if msg.get("language") in LANGS else "en-IN"
    user_id = _demo_user_key(msg.get("user_id", "demo-user"))

    # Manual phone-number/contact form asks the backend to validate before opening payment.
    if msg.get("type") == "prepare_demo_payment":
        payee = str(msg.get("payee", "")).strip()
        phone = norm_phone(payee)
        contact = next((name for name in CONTACTS if name.lower() == payee.lower()), None)
        try:
            amount = round(float(msg.get("amount", 0)), 2)
        except (TypeError, ValueError):
            amount = 0
        if not (phone or contact) or not (0 < amount <= DEMO_MAX_AMOUNT):
            await ws.send_json({"type": "demo_payment_prepared", "success": False, "reason": "invalid_details"})
            return
        wallet = get_demo_wallet(user_id)
        if amount > float(wallet.get("balance", DEMO_STARTING_BALANCE)):
            await ws.send_json({"type": "demo_payment_prepared", "success": False, "reason": "insufficient_demo_balance"})
            return
        normalized_payee = phone or contact
        await ws.send_json({"type": "demo_payment_prepared", "success": True, "payee": normalized_payee, "amount": amount, "mode": "SIMULATED"})
        await ws.send_json({"type": "action", "reply": PAY_READY.get(lang, PAY_READY["en-IN"]), "lang": lang, "actions": [{"tool": "prepare_payment", "payee": normalized_payee, "amount": amount}], "demo": True})
        await speak_out(ws, PAY_READY.get(lang, PAY_READY["en-IN"]), lang)
        return

    # Frontend calls this only after its payment/PIN screen's demo confirmation step.
    # PIN digits must never be included in this message.
    if msg.get("type") == "confirm_demo_payment":
        try:
            result = complete_demo_payment(user_id, msg.get("payee", ""), msg.get("amount", 0))
        except (TypeError, ValueError) as exc:
            result = {"success": False, "reason": "invalid_details", "message": str(exc)}
        await ws.send_json({"type": "demo_payment_result", **result})
        if result.get("success"):
            reply = {
                "en-IN": "Demo payment successful. No real money was transferred.",
                "hi-IN": "डेमो भुगतान सफल रहा। कोई असली पैसा ट्रांसफर नहीं हुआ।",
                "te-IN": "డెమో చెల్లింపు విజయవంతమైంది. నిజమైన డబ్బు బదిలీ కాలేదు.",
                "ta-IN": "டெமோ பணப்பரிவர்த்தனை வெற்றி. உண்மையான பணம் மாற்றப்படவில்லை.",
                "kn-IN": "ಡೆಮೋ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ. ನಿಜವಾದ ಹಣ ವರ್ಗಾಯಿಸಲಾಗಿಲ್ಲ.",
                "ml-IN": "ഡെമോ പേയ്‌മെന്റ് വിജയിച്ചു. യഥാർത്ഥ പണം കൈമാറിയിട്ടില്ല.",
                "bn-IN": "ডেমো পেমেন্ট সফল হয়েছে। আসল টাকা পাঠানো হয়নি।",
                "mr-IN": "डेमो पेमेंट यशस्वी झाले. खरे पैसे हस्तांतरित झाले नाहीत.",
                "gu-IN": "ડેમો ચુકવણી સફળ થઈ. વાસ્તવિક પૈસા ટ્રાન્સફર થયા નથી.",
                "pa-IN": "ਡੈਮੋ ਭੁਗਤਾਨ ਸਫਲ ਰਿਹਾ। ਅਸਲ ਪੈਸੇ ਟ੍ਰਾਂਸਫਰ ਨਹੀਂ ਹੋਏ।",
            }.get(lang, "Demo payment successful. No real money was transferred.")
        else:
            reply = {
                "en-IN": "The demo payment could not be completed. Please check the details and balance.",
                "hi-IN": "डेमो भुगतान पूरा नहीं हो सका। कृपया जानकारी और बैलेंस जाँचें।",
                "te-IN": "డెమో చెల్లింపు పూర్తి కాలేదు. వివరాలు, బ్యాలెన్స్ తనిఖీ చేయండి.",
                "ta-IN": "டெமோ பணப்பரிவர்த்தனை முடியவில்லை. விவரங்களையும் இருப்பையும் சரிபார்க்கவும்.",
                "kn-IN": "ಡೆಮೋ ಪಾವತಿ ಪೂರ್ಣಗೊಳ್ಳಲಿಲ್ಲ. ವಿವರ ಮತ್ತು ಬಾಕಿ ಪರಿಶೀಲಿಸಿ.",
                "ml-IN": "ഡെമോ പേയ്‌മെന്റ് പൂർത്തിയായില്ല. വിവരങ്ങളും ബാലൻസും പരിശോധിക്കുക.",
                "bn-IN": "ডেমো পেমেন্ট সম্পন্ন হয়নি। বিবরণ ও ব্যালেন্স পরীক্ষা করুন।",
                "mr-IN": "डेमो पेमेंट पूर्ण झाले नाही. तपशील आणि शिल्लक तपासा.",
                "gu-IN": "ડેમો ચુકવણી પૂર્ણ થઈ નથી. વિગતો અને બેલેન્સ તપાસો.",
                "pa-IN": "ਡੈਮੋ ਭੁਗਤਾਨ ਪੂਰਾ ਨਹੀਂ ਹੋਇਆ। ਵੇਰਵੇ ਅਤੇ ਬਕਾਇਆ ਜਾਂਚੋ।",
            }.get(lang, "The demo payment could not be completed.")
        await ws.send_json({"type": "action", "reply": reply, "lang": lang, "actions": [], "demo": True})
        await speak_out(ws, reply, lang)
        return

    if msg.get("type") == "get_demo_state":
        wallet = get_demo_wallet(user_id)
        await ws.send_json({"type": "demo_state", "balance": wallet["balance"], "transactions": wallet["transactions"], "currency": "INR", "mode": "SIMULATED"})
        return

    if msg.get("type") == "speak":

        await speak_out(ws, str(msg.get("text", ""))[:300], lang)

        return

    if msg.get("stage") == "pin" or msg.get("muted"):

        await ws.send_json({"type": "warn", "reason": "muted"})

        return

    try:

        wav = base64.b64decode(msg.get("audio", ""))

    except Exception:

        wav = b""

    if len(wav) < 4000:

        await ws.send_json({"type": "warn", "reason": "too_short"})

        return

    try:

        cands = await hear(wav, lang)

    except Exception as e:


        await ws.send_json({"type": "error", "message": f"STT failed: {e!r}"})

        return


    if not cands:                                                   # say so out loud, in the app language

        await ws.send_json({"type": "transcript", "text": "", "lang": lang})

        await ws.send_json({"type": "action", "reply": canned(lang), "lang": lang, "actions": []})

        await speak_out(ws, canned(lang), lang)

        return

    if any(re.fullmatch(r"[\d\s,.-]{4,}", c) for c in cands):      # a spoken PIN is never accepted

        await ws.send_json({"type": "transcript", "text": "••••", "lang": lang})

        await ws.send_json({"type": "action", "reply": canned(lang), "lang": lang, "actions": []})

        await speak_out(ws, canned(lang), lang)

        return

    await ws.send_json({"type": "transcript", "text": cands[0], "lang": lang})

    # Balance is private: only open the frontend's PIN-gated balance screen.
    # Never send the amount or wallet state before the frontend verifies the PIN.
    if is_balance_question(cands[0], lang):
        reply = BALANCE_OPEN.get(lang, BALANCE_OPEN["en-IN"])
        actions = [{"tool": "open_screen", "screen": "balance"}]
        await ws.send_json({"type": "action", "said": cands[0], "reply": reply,
                            "lang": lang, "actions": actions, "demo": True})
        await speak_out(ws, reply, lang)
        return

    said, reply, out_lang, actions = await understand(cands, lang, msg)

    await ws.send_json({"type": "action", "said": said, "reply": reply, "lang": out_lang, "actions": actions})

    await speak_out(ws, reply, out_lang)

@app.get("/health")

async def health():

    return {"ok": True}

@app.websocket("/ws")

async def ws_endpoint(ws: WebSocket):

    await ws.accept()

    try:

        while True:

            msg = json.loads(await ws.receive_text())

            try:

                await handle(ws, msg)

            except WebSocketDisconnect:

                raise

            except Exception as e:


                await ws.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:

        pass
