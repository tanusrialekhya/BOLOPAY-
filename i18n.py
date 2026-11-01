"""BolPay internationalization (i18n).

Supports exactly 10 user-facing languages:
English plus nine Indian languages.

English is the source language. The nine non-English dictionaries are stored
in translations.json. Missing translations are generated using the configured
Groq model and saved only after complete validation.

This module handles UI/message translation only. It does NOT perform speech
language detection, select Gnani voices, authorize payments, or execute UPI
transactions. Those responsibilities belong to the voice/backend and trusted
payment-service layers.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Iterable

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FILE = BASE_DIR / "translations.json"

MODEL = os.getenv(
    "TRANSLATE_MODEL",
    os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
)

LANGUAGE_CODES = {
    "English": "en-IN",
    "हिंदी": "hi-IN",
    "తెలుగు": "te-IN",
    "தமிழ்": "ta-IN",
    "ಕನ್ನಡ": "kn-IN",
    "മലയാളം": "ml-IN",
    "বাংলা": "bn-IN",
    "मराठी": "mr-IN",
    "ગુજરાતી": "gu-IN",
    "ਪੰਜਾਬੀ": "pa-IN",
}

LANGUAGE_NAMES = {
    "English": "English",
    "हिंदी": "Hindi",
    "తెలుగు": "Telugu",
    "தமிழ்": "Tamil",
    "ಕನ್ನಡ": "Kannada",
    "മലയാളം": "Malayalam",
    "বাংলা": "Bengali",
    "मराठी": "Marathi",
    "ગુજરાતી": "Gujarati",
    "ਪੰਜਾਬੀ": "Punjabi",
}

CODE_TO_NAME = {
    code: name for name, code in LANGUAGE_CODES.items()
}

NON_ENGLISH_LANGUAGES = tuple(
    name for name in LANGUAGE_CODES if name != "English"
)

EN_TEXT = r"""brand|BolPay
nav_home|Home
nav_scan|Scan & Pay
nav_tx|Transactions
nav_help|Help
signin|Sign in
h1a|Speak. Pay.
h1b|Simplify.
sub|Your voice-powered payment assistant
start|Get Started
hello|Hello
how|How can I help you today?
tap|Tap and speak
tile_scan|Scan QR
tile_pay|Pay
tile_hist|History
tile_bal|Balance
say_like|Say things like
ex1|Pay ₹500 to Amma
ex2|Show my balance
ex3|Open history
ex4|Scan QR code
bub_home|Hi! Tap the mic and tell me what you need.
bub_welcome|Nice to meet you! What should I call you?
bub_scan|Show me a QR code and I will read it for you.
bub_pay|Tell me the amount and recipient. I will help you review the payment.
bub_pin|Enter your PIN on the screen. Never say your PIN aloud.
bub_hist|Here are your recent transactions.
bub_bal|Authenticate securely to see your balance.
bub_help|Try saying one of these. I am here to help.
bub_ok|Your payment is confirmed.
bub_bad|Something went wrong. I can help you check what happened.
name_q|What should we call you?
name|Your name
cont|Continue
scan_title|Scan QR
scan_hint|Point the camera at a QR code
cam|Camera
gallery|Gallery
take_photo|Take photo
upload|Upload QR image
qr_ok|QR code detected
qr_fail|Could not read this QR code. Try again.
qr_pay|Pay this person
qr_check|Check the recipient name and details before paying.
qr_text|QR text
pay_title|Pay
pay_to|Pay to
amount|Amount (₹)
note|Add a note (optional)
pay_now|Continue to payment
step1|Details
step2|Authentication
step3|Status
pin_label|Enter your PIN securely on the screen
confirm_pay|Confirm this payment
cancel|Cancel
bad_pin|The PIN was not accepted. Try again.
tries_left|attempts left
too_many|Too many unsuccessful attempts. Payment stopped.
no_funds|There may not be enough balance for this payment.
success|Payment confirmed
paid_to|Paid to
new_bal|New balance
sim|This is a demo. No real money moved.
retry|Try again
done|Done
view_hist|View history
back|Back to Home
hist_title|Transaction history
empty|No transactions yet
received|Received
completed|Completed
bal_title|Account balance
holder|Account holder
acc|Account number
avail|Available balance
hide|Hide balance
unlock|Unlock
pin_bal|Authenticate securely to view your balance
st_listen|Listening…
st_proc|Processing…
st_speak|Speaking…
st_pin|Microphone is off during secure PIN entry
mic_denied|Please allow microphone access to use voice features
st_err|Cannot reach the voice service. Please try again.
help_title|Help
try|Try saying
font|Text size
small|Small
medium|Medium
large|Large
lang_tip|To change language, say: Change my language
say_hello|Hello! How can I help you?
say_ok|Your payment of ₹{amt} to {name} is confirmed.
say_bad|The PIN was not accepted. Please try again.
say_cancel|The payment was stopped after too many unsuccessful attempts.
say_nofunds|There may not be enough balance. I have not confirmed a payment.
c_Amma|Amma
c_Dad|Dad
c_Rahul|Rahul
c_Priya|Priya
c_Shopkeeper|Shopkeeper
language_mismatch|You selected {language}. Please speak in {language}, or ask to change your language.
language_switch_ask|You asked to change the language to {language}. Do you want to continue?
language_switch_confirm|Your language is now {language}.
language_switch_cancel|Your language has not been changed.
language_not_supported|Sorry, that language is not available.
repeat_slowly|I did not understand. Please say that again slowly.
speak_selected_language|Please speak in your selected language: {language}.
recipient_unclear|I am not sure who should receive the money. Please say the recipient's name again.
amount_unclear|I did not understand the amount. Please say the amount again.
payment_review|Please check the recipient and amount before confirming.
payment_cancelled|The payment was cancelled. No payment was made.
payment_pending|Your payment is still pending. Please do not try again yet.
payment_failed|The payment service reports that the payment failed.
payment_status_unknown|I cannot confirm the payment status yet. Please check the transaction status before trying again.
payment_not_confirmed|The payment has not been confirmed. I will not say that it succeeded.
refund_help|I can help you raise a support request about this refund.
money_deducted_help|If money was deducted but the recipient did not receive it, I can help you contact support.
support_offer|Would you like me to create a support request for you?
support_consent|May I share the relevant transaction details and your issue with our support team?
support_created|Your support request was created. Your ticket number is {ticket}.
support_not_created|I could not create the support request. Please try again or contact support.
support_status|Your support request status is {status}.
support_human_requested|I will help you contact a human support representative.
support_wait|Your request is waiting for the support team.
transaction_not_found|I could not find that transaction.
transaction_filter|Tell me the recipient, date, or amount you want to search for.
contact_saved|The contact was saved.
contact_save_confirm|Do you want me to save {name} as a contact?
repeat_payment_confirm|Do you want to review the previous payment again? I will not repeat it without your confirmation.
pin_never_speak|For your safety, never say or share your PIN, OTP, or password. Enter sensitive details only in the secure screen.
voice_retry|I could not connect to the voice service. Please try again.
service_unavailable|This service is temporarily unavailable. Please try again later.
"""

EN = dict(
    line.split("|", 1)
    for line in EN_TEXT.strip().splitlines()
    if "|" in line
)

_mem: Dict[str, Dict[str, str]] = {}


def available_languages():
    """Return all 10 selectable languages and their locale codes."""
    return [
        {
            "label": label,
            "code": code,
            "english_name": LANGUAGE_NAMES[label],
        }
        for label, code in LANGUAGE_CODES.items()
    ]


def normalize_language(language: str) -> str:
    """Accept a display label or locale code and return the display label."""
    if not isinstance(language, str):
        raise TypeError("Language must be a string.")

    value = language.strip()

    if value in LANGUAGE_CODES:
        return value

    if value in CODE_TO_NAME:
        return CODE_TO_NAME[value]

    raise ValueError(
        f"Unsupported language {language!r}. "
        f"Supported codes: {', '.join(LANGUAGE_CODES.values())}"
    )


def language_code(language: str) -> str:
    """Return the locale code for a language."""
    return LANGUAGE_CODES[normalize_language(language)]


def language_english_name(language: str) -> str:
    """Return the English name of a selected language."""
    return LANGUAGE_NAMES[normalize_language(language)]


def _read() -> dict:
    """Read translations.json and report invalid JSON."""
    if not FILE.exists():
        return {}

    try:
        with FILE.open("r", encoding="utf-8") as handle:
            result = json.load(handle)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"{FILE.name} contains invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError(
            f"{FILE.name} must contain a JSON object."
        )

    return result


def _write_atomic(data: dict) -> None:
    """Write safely so an interrupted write does not corrupt the JSON file."""
    FILE.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix="translations_",
        suffix=".tmp",
        dir=str(FILE.parent),
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                data,
                handle,
                ensure_ascii=False,
                indent=2,
            )
            handle.write("\n")

        os.replace(temp_name, FILE)

    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _placeholders(text: str) -> list[str]:
    return sorted(
        re.findall(
            r"\{[A-Za-z_][A-Za-z0-9_]*\}",
            text,
        )
    )


def _validate_translation(
    key: str,
    source: str,
    translated: str,
) -> str:
    """Check that a translation is non-empty and preserves placeholders."""
    if not isinstance(translated, str) or not translated.strip():
        raise ValueError(
            f"Empty translation for key {key!r}."
        )

    translated = translated.strip()

    if _placeholders(source) != _placeholders(translated):
        raise ValueError(
            f"Placeholder mismatch for key {key!r}."
        )

    return translated


def _chat(prompt: str) -> str:
    """Call the configured Groq model for missing fixed UI translations."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    client = Groq(api_key=api_key)

    last_error = None

    for extra in (
        {"extra_body": {"reasoning_effort": "low"}},
        {},
    ):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0,
                max_tokens=6000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                **extra,
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError(
                    "Groq returned an empty translation response."
                )

            return content

        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        f"Groq translation request failed: {last_error}"
    ) from last_error


def _extract_json_object(raw: str) -> dict:
    """Parse JSON, allowing an optional Markdown code fence."""
    text = raw.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
            count=1,
        )

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end < start:
        raise ValueError(
            "The translation response did not contain a JSON object."
        )

    result = json.loads(text[start:end + 1])

    if not isinstance(result, dict):
        raise ValueError(
            "The translation response must be a JSON object."
        )

    return result


def _translate(language: str, keys: Iterable[str]) -> dict:
    """Translate all requested keys, rejecting incomplete batches."""
    language = normalize_language(language)

    if language == "English":
        return {
            key: EN[key]
            for key in keys
        }

    target_language = LANGUAGE_NAMES[language]
    keys = list(keys)
    translated_all = {}

    batch_size = 25

    for offset in range(0, len(keys), batch_size):
        batch_keys = keys[offset:offset + batch_size]

        source_batch = {
            key: EN[key]
            for key in batch_keys
        }

        prompt = (
            f"You are a professional translator for BolPay, a voice-first "
            f"digital payment assistant for older adults and people with limited "
            f"digital literacy. Translate the values from English into "
            f"{target_language}. Use simple, respectful, natural everyday "
            f"language suitable for both on-screen text and text-to-speech. "
            f"Use the target language's normal writing system. Do not translate "
            f"brand names, personal names, PIN, OTP, QR, or UPI when keeping "
            f"them in Latin script is clearer and safer. Preserve all numbers, "
            f"₹ symbols, punctuation where meaningful, and every placeholder "
            f"such as {{amt}}, {{name}}, {{language}}, {{ticket}}, and {{status}} "
            f"exactly. Never change the meaning of payment, authentication, "
            f"cancellation, pending, failure, or support messages. Do not claim "
            f"a payment succeeded unless the source says it is confirmed. "
            f"Return ONLY a valid JSON object with exactly the same keys and "
            f"translated string values. No commentary.\n\n"
            f"{json.dumps(source_batch, ensure_ascii=False)}"
        )

        last_error = None
        batch_result = None

        for attempt in range(3):
            try:
                raw = _chat(prompt)
                candidate = _extract_json_object(raw)

                if set(candidate.keys()) != set(source_batch.keys()):
                    missing = sorted(
                        set(source_batch) - set(candidate)
                    )
                    extra = sorted(
                        set(candidate) - set(source_batch)
                    )

                    raise ValueError(
                        f"Key mismatch. Missing={missing}; extra={extra}"
                    )

                validated = {}

                for key, source in source_batch.items():
                    validated[key] = _validate_translation(
                        key,
                        source,
                        candidate[key],
                    )

                batch_result = validated
                break

            except Exception as exc:
                last_error = exc

        if batch_result is None:
            raise RuntimeError(
                f"Could not translate {language}, batch "
                f"{offset // batch_size + 1}: {last_error}"
            ) from last_error

        translated_all.update(batch_result)

    if set(translated_all) != set(keys):
        raise RuntimeError(
            f"Translation is incomplete for {language}."
        )

    return translated_all


def validate_language(language: str) -> dict:
    """Report missing or invalid translations without generating them."""
    language = normalize_language(language)

    if language == "English":
        return {
            "language": language,
            "code": language_code(language),
            "total": len(EN),
            "translated": len(EN),
            "missing": [],
            "valid": True,
        }

    translations = _read().get(language, {})

    if not isinstance(translations, dict):
        translations = {}

    missing = []
    invalid = []

    for key, source in EN.items():
        value = translations.get(key)

        if not isinstance(value, str) or not value.strip():
            missing.append(key)
            continue

        try:
            _validate_translation(
                key,
                source,
                value,
            )

        except ValueError:
            invalid.append(key)

    return {
        "language": language,
        "code": language_code(language),
        "total": len(EN),
        "translated": len(EN) - len(missing) - len(invalid),
        "missing": missing,
        "invalid": invalid,
        "valid": not missing and not invalid,
    }


def ready(language: str) -> bool:
    """Return True only if every source message has a valid translation."""
    language = normalize_language(language)

    if language == "English":
        return True

    if language in _mem:
        translations = _mem[language]
    else:
        translations = _read().get(language, {})

    if not isinstance(translations, dict):
        return False

    for key, source in EN.items():
        try:
            _validate_translation(
                key,
                source,
                translations.get(key),
            )

        except (ValueError, TypeError):
            return False

    return True


def get(language: str) -> dict:
    """Return a complete translation dictionary.

    Missing translations are generated using Groq and saved only after
    validation. Non-English languages do not silently fall back to English.
    """
    language = normalize_language(language)

    if language == "English":
        return EN.copy()

    if language in _mem and ready(language):
        return _mem[language].copy()

    data = _read()
    existing = data.get(language, {})

    if not isinstance(existing, dict):
        existing = {}

    existing = {
        key: value
        for key, value in existing.items()
        if key in EN
        and isinstance(value, str)
        and value.strip()
    }

    missing = []

    for key, source in EN.items():
        try:
            _validate_translation(
                key,
                source,
                existing.get(key),
            )

        except (ValueError, TypeError):
            missing.append(key)

    if missing:
        generated = _translate(
            language,
            missing,
        )
        existing.update(generated)

    for key, source in EN.items():
        _validate_translation(
            key,
            source,
            existing.get(key),
        )

    data[language] = existing

    _write_atomic(data)

    _mem[language] = existing.copy()

    return existing.copy()


def clear_cache() -> None:
    """Clear the in-memory translation cache."""
    _mem.clear()


if __name__ == "__main__":
    print(
        f"BolPay supports {len(LANGUAGE_CODES)} languages."
    )

    print(
        f"Source strings: {len(EN)}"
    )

    print(
        f"Translation model: {MODEL}"
    )

    print()

    for language, code in LANGUAGE_CODES.items():

        if language == "English":
            print(
                f"{code}  {language}: OK "
                f"(source language, {len(EN)} strings)"
            )
            continue

        try:
            get(language)

            print(
                f"{code}  {language}: OK "
                f"({len(EN)} strings)"
            )

        except Exception as exc:
            report = validate_language(language)

            print(
                f"{code}  {language}: INCOMPLETE "
                f"({len(report['missing'])} missing, "
                f"{len(report['invalid'])} invalid) - {exc}"
            )
