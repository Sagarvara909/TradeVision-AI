"""
LLM Explainable Report service.

Takes the output of the risk/confidence pipeline and asks Gemini to turn it
into a plain-language report. The model is told to EXPLAIN the numbers it is
given, never to advise, predict, or invent new figures.

Uses the current `google-genai` SDK (NOT the retired `google-generativeai`).

    pip uninstall google-generativeai
    pip install google-genai
"""

import logging
import re
import time
from typing import Any

from google import genai
from google.genai import errors, types

from app.core.config import settings

logger = logging.getLogger(__name__)

# Model names change over time. Prefer setting `gemini_model` in config.py
# (and optionally GEMINI_MODEL in .env); this is only the fallback.
DEFAULT_MODEL = "gemini-3.8-flash"
# Tried in order if the primary model is overloaded (503/429) or missing (404).
# Fill this from `python try_models.py` (it shows which models work for your key).
# Can also be set in config.py as: gemini_fallback_models: list[str] = [...]
DEFAULT_FALLBACKS: list[str] = []
RETRIES_PER_MODEL = 3
RETRYABLE_CODES = {429, 500, 503}
SWITCH_MODEL_CODES = {404, 429, 500, 503}

DISCLAIMER = (
    "Disclaimer: This report is generated for educational and decision-support "
    "purposes only. It is not financial advice, and it does not predict future "
    "price movements."
)

REPORT_PROMPT_TEMPLATE = """You are a financial analysis assistant generating an EXPLAINABLE trading decision-support report.

STRICT RULES:
- You do NOT give trading advice, predictions, price targets, or buy/sell/hold recommendations.
- Use ONLY the numbers provided below. Never invent, estimate, or round to new figures.
- If a value is "N/A", say the data was unavailable instead of guessing.
- Explain what the data shows and why, honestly, including uncertainty.

ANALYSIS DATA FOR {symbol}:

TECHNICAL INDICATORS:
- Trend: {trend}
- RSI (14): {rsi}
- EMA 20: {ema20}
- EMA 50: {ema50}
- MACD: {macd} (Signal: {macd_signal}, Histogram: {macd_histogram})
- Support: {support}
- Resistance: {resistance}
- Volume: {volume_ratio}x average (above average: {above_average_volume})
- Volatility (avg daily range as % of price): {volatility_pct}

NEWS SENTIMENT:
- Label: {sentiment_label}
- Score: {sentiment_score} (range -1 to +1)
- Based on {article_count} recent articles

CONFIDENCE SCORE: {confidence_score}/100
RISK LEVEL: {risk_level}

REASONING TRAIL (how the confidence score was calculated):
{reasoning_list}

Note: the confidence score measures how well the signals AGREE with each other.
It is NOT a probability that the price will rise or fall.

Write a clear, well-organised report (300-400 words) with these sections:
**Summary** - one paragraph, plain-language overview of what the data shows for {symbol}
**Technical Picture** - what the indicators show, in plain English
**Sentiment Context** - how the news sentiment fits into the picture
**Confidence & Risk** - explain the score and risk level, referencing the reasoning trail
**Caveats** - state clearly that this is not financial advice and is for educational purposes only

Use bold text for section names (like **Summary**). Do not use markdown headers with #.
Write in a professional but accessible tone."""


class LLMServiceError(Exception):
    """Raised when report generation fails. The message is safe to show to users."""


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Create the Gemini client once, on first use (not at import time)."""
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise LLMServiceError("Gemini API key is not configured.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _model_name() -> str:
    return getattr(settings, "gemini_model", None) or DEFAULT_MODEL


def _model_chain() -> list[str]:
    """Primary model first, then fallbacks, without duplicates."""
    fallbacks = getattr(settings, "gemini_fallback_models", None) or DEFAULT_FALLBACKS
    chain: list[str] = []
    for m in [_model_name(), *fallbacks]:
        if m and m not in chain:
            chain.append(m)
    return chain


def _val(data: dict[str, Any], key: str) -> Any:
    """Return data[key], or 'N/A' if it is missing or None."""
    value = data.get(key)
    return "N/A" if value is None else value


def build_prompt(risk_analysis: dict[str, Any]) -> str:
    """Fill the prompt template from the risk-analysis dict."""
    sentiment = risk_analysis.get("sentiment") or {}
    reasoning = risk_analysis.get("reasoning") or []

    return REPORT_PROMPT_TEMPLATE.format(
        symbol=_val(risk_analysis, "symbol"),
        trend=_val(risk_analysis, "trend"),
        rsi=_val(risk_analysis, "rsi"),
        ema20=_val(risk_analysis, "ema20"),
        ema50=_val(risk_analysis, "ema50"),
        macd=_val(risk_analysis, "macd"),
        macd_signal=_val(risk_analysis, "macd_signal"),
        macd_histogram=_val(risk_analysis, "macd_histogram"),
        support=_val(risk_analysis, "support"),
        resistance=_val(risk_analysis, "resistance"),
        volume_ratio=_val(risk_analysis, "volume_ratio"),
        above_average_volume=_val(risk_analysis, "above_average_volume"),
        volatility_pct=_val(risk_analysis, "volatility_pct"),
        sentiment_label=_val(sentiment, "label"),
        sentiment_score=_val(sentiment, "score"),
        article_count=_val(sentiment, "article_count"),
        confidence_score=_val(risk_analysis, "confidence_score"),
        risk_level=_val(risk_analysis, "risk_level"),
        reasoning_list="\n".join(f"- {r}" for r in reasoning) or "- (none provided)",
    )


def find_unsupported_numbers(report: str, reference_text: str) -> list[str]:
    """
    Light safety check: return numbers that appear in the report but nowhere in
    `reference_text`. Pass the actual PROMPT here (not just the raw data dict) -
    the prompt's own wording ("RSI (14)", "-1 to +1", "/100", "300-400 words")
    contains numbers that are legitimate template text, not hallucinations, and
    comparing against the data dict alone flags them as false positives.
    An empty list means every number in the report traces back to something the
    model was actually given.
    """
    source_numbers = set(re.findall(r"\d+\.?\d*", reference_text))

    unsupported = []
    for num in set(re.findall(r"\d+\.?\d*", report)):
        clean = num.rstrip(".")  # trailing '.' from end-of-sentence digits, e.g. "...in 2024."
        if clean in source_numbers or num in source_numbers:
            continue
        try:
            if any(abs(float(clean) - float(s)) < 0.01 for s in source_numbers if s):
                continue
        except ValueError:
            pass
        unsupported.append(num)
    return sorted(unsupported)


def generate_report(risk_analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Generate an explainable report from the risk-analysis output
    (the RiskAnalysisResponse shape, as a dict via `.model_dump()`).

    Tries the primary model with retries. If it stays overloaded (503/429) or
    is missing (404), moves on to the next model in the fallback chain.

    Returns:
        {
            "report": str,                 # the text, with disclaimer appended
            "model": str,                  # which Gemini model actually wrote it
            "unsupported_numbers": list,   # numbers not found in the input (should be empty)
        }

    Raises:
        LLMServiceError: with a user-safe message if every model fails.
    """
    prompt = build_prompt(risk_analysis)
    client = _get_client()

    config = types.GenerateContentConfig(
        temperature=0.3,          # low = more faithful to the given numbers
        max_output_tokens=2048,   # headroom, since thinking tokens count too
    )

    last_message = "Could not generate the report. Please try again."

    for model in _model_chain():
        for attempt in range(1, RETRIES_PER_MODEL + 1):
            try:
                response = client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                text = (response.text or "").strip()
                if not text:
                    last_message = "The AI model returned an empty response. Please try again."
                    logger.warning("Empty response from %s", model)
                    break  # try next model

                unsupported = find_unsupported_numbers(text, prompt)
                if unsupported:
                    logger.warning("Report contains numbers not in input: %s", unsupported)

                return {
                    "report": f"{text}\n\n{DISCLAIMER}",
                    "model": model,
                    "unsupported_numbers": unsupported,
                }

            except errors.APIError as exc:
                code = getattr(exc, "code", None)
                logger.error("%s -> API error %s (attempt %d/%d)", model, code, attempt, RETRIES_PER_MODEL)

                if code in (401, 403):
                    # Key/project problem: no other model will fix it.
                    raise LLMServiceError(
                        "The AI service rejected the API key or project access. "
                        "Check GEMINI_API_KEY and that the Gemini API is enabled."
                    ) from exc

                if code == 404:
                    last_message = f"AI model '{model}' was not found. Check the model name."
                elif code == 429:
                    last_message = "The AI service is rate-limited right now. Please try again shortly."
                else:
                    last_message = "The AI service is temporarily busy. Please try again in a minute."

                if code in RETRYABLE_CODES and attempt < RETRIES_PER_MODEL:
                    time.sleep(min(2 ** attempt, 8))  # 2s, 4s
                    continue
                if code in SWITCH_MODEL_CODES:
                    break  # give up on this model, try the next one
                raise LLMServiceError(last_message) from exc

            except Exception as exc:  # network errors, SDK errors, etc.
                logger.exception("Unexpected error calling Gemini")
                raise LLMServiceError("Could not generate the report. Please try again.") from exc

    raise LLMServiceError(last_message)