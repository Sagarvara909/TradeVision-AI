"""
AI Chat service — grounded follow-up Q&A on an already-generated report.

Reuses llm_service's Gemini client and model-fallback chain, so there is one
place that knows how to talk to Gemini, retry on 503/429, and fall back to a
secondary model when the primary is overloaded. The chat prompt is
deliberately narrow: it is given the report's full indicator data and the
generated report text, and told to answer ONLY from that — never to add new
numbers, predictions or advice. This keeps the chat consistent with the
project's core explainability thesis.
"""

import logging
from typing import Any

from google.genai import types

from app.services.llm_service import (
    LLMServiceError,
    _get_client,
    _model_chain,
    find_unsupported_numbers,
)

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are answering follow-up questions about a trading chart analysis report the person is already looking at. Help them understand it better.

STRICT RULES:
- Answer ONLY using the data and report text given below. Never invent, estimate, or add new numbers.
- You do NOT give trading advice, predictions, price targets, or buy/sell/hold recommendations, even if asked directly. If asked for advice, explain that you can only explain the existing analysis, not advise on decisions.
- If the data below doesn't contain what's needed to answer, say so honestly rather than guessing.
- Keep answers conversational and concise (2-4 sentences), unless the question genuinely needs a longer breakdown.

REPORT DATA FOR {symbol}:
{indicators_block}

FULL REPORT TEXT:
{report_text}

The conversation so far, and the new question, follow below."""

MAX_HISTORY_TURNS = 10  # keep the prompt small; older turns are dropped, not lost (still saved in DB)


def _format_indicators(indicators: dict[str, Any]) -> str:
    sentiment = indicators.get("sentiment") or {}
    reasoning = indicators.get("reasoning") or []
    lines = [
        f"Trend: {indicators.get('trend', 'N/A')}",
        f"RSI (14): {indicators.get('rsi', 'N/A')}",
        f"EMA 20: {indicators.get('ema20', 'N/A')}",
        f"EMA 50: {indicators.get('ema50', 'N/A')}",
        f"MACD: {indicators.get('macd', 'N/A')} "
        f"(Signal: {indicators.get('macd_signal', 'N/A')}, Histogram: {indicators.get('macd_histogram', 'N/A')})",
        f"Support: {indicators.get('support', 'N/A')}",
        f"Resistance: {indicators.get('resistance', 'N/A')}",
        f"Volume: {indicators.get('volume_ratio', 'N/A')}x average "
        f"(above average: {indicators.get('above_average_volume', 'N/A')})",
        f"Volatility: {indicators.get('volatility_pct', 'N/A')}%",
        f"News sentiment: {sentiment.get('label', 'N/A')} "
        f"(score {sentiment.get('score', 'N/A')}, {sentiment.get('article_count', 'N/A')} articles)",
        f"Confidence score: {indicators.get('confidence_score', 'N/A')}/100",
        f"Risk level: {indicators.get('risk_level', 'N/A')}",
        "Reasoning trail:",
        *[f"  - {r}" for r in reasoning],
    ]
    return "\n".join(lines)


def answer_question(
    indicators: dict[str, Any],
    report_text: str,
    history: list[dict[str, str]],
    question: str,
) -> dict[str, Any]:
    """
    Answer a follow-up question grounded in one report's data.

    `history` is prior turns as [{"role": "user"|"assistant", "content": "..."}],
    oldest first. Only the last MAX_HISTORY_TURNS are sent to the model, to
    keep the prompt small — the full history still lives in the database.

    Returns {"answer": str, "model": str, "unsupported_numbers": list[str]}.
    `unsupported_numbers` flags any number in the answer that doesn't trace
    back to the report data or prompt — should normally be empty.

    Raises LLMServiceError (same type report generation raises) on failure,
    so callers can handle both the same way.
    """
    symbol = indicators.get("symbol", "the symbol")
    system_block = CHAT_SYSTEM_PROMPT.format(
        symbol=symbol,
        indicators_block=_format_indicators(indicators),
        report_text=report_text or "(no report text available)",
    )

    turns = [system_block]
    for turn in history[-MAX_HISTORY_TURNS:]:
        prefix = "User" if turn.get("role") == "user" else "Assistant"
        turns.append(f"{prefix}: {turn.get('content', '')}")
    turns.append(f"User: {question}")
    full_prompt = "\n\n".join(turns)

    client = _get_client()
    config = types.GenerateContentConfig(temperature=0.3, max_output_tokens=1024)

    last_message = "Could not answer right now. Please try again."
    for model in _model_chain():
        try:
            response = client.models.generate_content(
                model=model, contents=full_prompt, config=config
            )
            text = (response.text or "").strip()
            if not text:
                last_message = "The AI returned an empty response. Please try again."
                continue

            unsupported = find_unsupported_numbers(text, full_prompt)
            if unsupported:
                logger.warning("Chat answer contains unsupported numbers: %s", unsupported)

            return {"answer": text, "model": model, "unsupported_numbers": unsupported}

        except Exception as exc:
            logger.warning("Chat answer failed on model %s: %s", model, exc)
            last_message = "Could not answer right now. Please try again."
            continue

    raise LLMServiceError(last_message)