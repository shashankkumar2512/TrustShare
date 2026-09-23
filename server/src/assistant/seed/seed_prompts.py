"""
Seed default AI Assistant prompts.
"""

import logging
from sqlalchemy.orm import Session

from src.entities.assistant_prompt import AssistantPrompt

logger = logging.getLogger(__name__)


DEFAULT_PROMPTS = [
    {
        "prompt_key": "SYSTEM_PROMPT",
        "prompt_text": (
            "You are TrustShare Assistant, a helpful AI for the TrustShare secure "
            "file-sharing platform. You help users manage their files, storage, "
            "shares, and account.\n\n"
            "GUIDELINES:\n"
            "- Be concise, friendly, and professional\n"
            "- When users ask about their data, USE the available functions to "
            "fetch real information — never invent data\n"
            "- If a function returns no results, tell the user clearly\n"
            "- Format numbers, sizes, and dates in a human-friendly way\n"
            "- If a user asks something outside your capabilities (like modifying "
            "files, deleting shares, or changing passwords), politely explain "
            "what they can do in the app instead\n"
            "- Never expose API keys, tokens, passwords, or internal IDs\n"
            "- If uncertain about intent, ask a clarifying question\n\n"
            "You have access to the user's files, storage info, shares, sessions, "
            "notifications, and profile via function calls. Use them to give "
            "accurate answers."
        ),
        "description": "Main system prompt defining bot personality and rules",
    },
    {
        "prompt_key": "WELCOME_MESSAGE",
        "prompt_text": (
            "👋 Hi there! I'm your TrustShare Assistant. I can help you find files, "
            "check your storage, review shares, and answer questions about your "
            "account. What would you like to know?"
        ),
        "description": "Initial message shown when opening a new chat",
    },
    {
        "prompt_key": "NOT_CONFIGURED",
        "prompt_text": (
            "The AI Assistant hasn't been configured yet. An administrator needs "
            "to set up the AI provider API key in the admin panel before chat is "
            "available."
        ),
        "description": "Message shown when API key is missing",
    },
    {
        "prompt_key": "RATE_LIMITED",
        "prompt_text": (
            "You're sending messages too quickly. Please wait a moment before "
            "trying again."
        ),
        "description": "Message shown when user exceeds rate limit",
    },
    {
        "prompt_key": "ERROR_FALLBACK",
        "prompt_text": (
            "Sorry, I ran into a problem processing your request. Please try "
            "again, or rephrase your question."
        ),
        "description": "Generic error fallback",
    },
    {
        "prompt_key": "MESSAGE_TOO_LONG",
        "prompt_text": ("Your message is too long. Please shorten it and try again."),
        "description": "Shown when user message exceeds max length",
    },
    {
        "prompt_key": "ASSISTANT_DISABLED",
        "prompt_text": (
            "The AI Assistant is currently disabled. Please contact your "
            "administrator."
        ),
        "description": "Shown when ENABLE_ASSISTANT config is false",
    },
    {
        "prompt_key": "NO_RESPONSE",
        "prompt_text": (
            "I'm not sure how to respond to that. Could you rephrase your question?"
        ),
        "description": "Shown when LLM returns empty content with no function call",
    },
    {
        "prompt_key": "LOOP_LIMIT",
        "prompt_text": (
            "I got stuck trying to answer that. Please try rephrasing your question "
            "more simply."
        ),
        "description": "Shown when max function call iterations reached (safety limit)",
    },
    {
        "prompt_key": "CONVERSATION_NOT_FOUND",
        "prompt_text": (
            "That conversation doesn't exist or you don't have access to it."
        ),
        "description": "Shown when user tries to access a conversation they don't own",
    },
    {
        "prompt_key": "TITLE_GENERATION_SYSTEM",
        "prompt_text": (
            "You generate a short 3-5 word title for a chat conversation. "
            "Return ONLY the title, no quotes, no punctuation, no explanation."
        ),
        "description": "System prompt for auto-generating conversation titles",
    },
    {
        "prompt_key": "TITLE_GENERATION_USER",
        "prompt_text": "Generate a title for this message: {message}",
        "description": "User prompt template for title generation (use {message} placeholder)",
    },
    {
        "prompt_key": "LLM_RATE_LIMITED",
        "prompt_text": (
            "🚫 The AI service has hit its rate limit for now. "
            "Please try again in a few minutes. If this happens often, "
            "your administrator can switch to a different model in Settings."
        ),
        "description": "Shown when LLM provider returns 429 rate limit error",
    },
    {
        "prompt_key": "LLM_INVALID_KEY",
        "prompt_text": (
            "🔑 The AI service API key is invalid or expired. "
            "Please contact your administrator to update it."
        ),
        "description": "Shown when LLM returns 401 unauthorized",
    },
    {
        "prompt_key": "LLM_TIMEOUT",
        "prompt_text": (
            "⏱️ The AI is taking longer than usual to respond. "
            "This might be due to a complex query. Please try again or "
            "simplify your question."
        ),
        "description": "Shown when LLM request times out",
    },
]


def seed_prompts(db: Session) -> int:
    added = 0

    for prompt_data in DEFAULT_PROMPTS:
        existing = (
            db.query(AssistantPrompt)
            .filter(AssistantPrompt.prompt_key == prompt_data["prompt_key"])
            .first()
        )

        if existing:
            continue  # Never overwrite — admin may have customized

        prompt = AssistantPrompt(**prompt_data)
        db.add(prompt)
        added += 1

    if added > 0:
        db.commit()

    return added
