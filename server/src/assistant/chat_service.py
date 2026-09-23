"""
Chat Service — TrustShare AI Assistant
Main orchestration layer for chat interactions.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.entities.user import User
from src.entities.assistant_function import AssistantFunction
from src.entities.assistant_prompt import AssistantPrompt

from src.assistant import config_service, conversation_service, functions
from src.assistant.llm_client import LLMClient, LLMError, LLMNotConfiguredError

logger = logging.getLogger(__name__)


DEFAULT_MAX_ITERATIONS = 5


def _load_active_tools(db: Session) -> list[dict]:
    """Load all active function definitions from DB as OpenAI tool format."""
    fn_rows = (
        db.query(AssistantFunction)
        .filter(AssistantFunction.is_active == True)
        .order_by(AssistantFunction.display_order)
        .all()
    )

    tools = []
    for row in fn_rows:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": row.function_name,
                    "description": row.description,
                    "parameters": row.parameters_schema
                    or {"type": "object", "properties": {}},
                },
            }
        )
    return tools


def _get_prompt(db: Session, prompt_key: str, fallback: str = "") -> str:
    """Load a prompt from DB."""
    row = (
        db.query(AssistantPrompt)
        .filter(
            AssistantPrompt.prompt_key == prompt_key,
            AssistantPrompt.is_active == True,
        )
        .first()
    )
    return row.prompt_text if row else fallback


def process_chat(
    db: Session,
    user: User,
    user_message: str,
    conversation_id: Optional[int] = None,
) -> dict:
    """
    Process a single user chat turn.

    Returns dict with:
        - conversation_id
        - message: assistant's text response
        - function_calls: list of {name, args, result} for any functions invoked
        - is_new_conversation: bool
        - tokens_used
        - model_used
    """
    if not config_service.get_bool(db, "ENABLE_ASSISTANT", False):
        return {
            "error": True,
            "message": _get_prompt(
                db,
                "ASSISTANT_DISABLED",
                "AI Assistant is currently disabled.",
            ),
        }

    if not config_service.is_assistant_configured(db):
        return {
            "error": True,
            "message": _get_prompt(
                db,
                "NOT_CONFIGURED",
                "AI Assistant is not configured. Contact your administrator.",
            ),
        }

    max_len = config_service.get_int(db, "MAX_MESSAGE_LENGTH", 2000)
    if len(user_message) > max_len:
        return {
            "error": True,
            "message": _get_prompt(
                db,
                "MESSAGE_TOO_LONG",
                f"Your message exceeds {max_len} characters.",
            ),
        }

    is_new_conversation = False
    if conversation_id:
        conv = conversation_service.get_conversation(db, conversation_id, user.id)
        if not conv:
            return {
                "error": True,
                "message": _get_prompt(
                    db,
                    "CONVERSATION_NOT_FOUND",
                    "Conversation not found or you don't have access to it.",
                ),
            }
    else:
        conv = conversation_service.create_conversation(db, user.id)
        is_new_conversation = True

    conversation_service.add_message(db, conv.id, role="user", content=user_message)

    system_prompt = _get_prompt(
        db,
        "SYSTEM_PROMPT",
        "You are a helpful assistant.",
    )
    llm_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    tools = _load_active_tools(db)

    client = LLMClient(db)
    function_calls_log = []
    total_tokens = 0
    final_model = None

    try:
        max_iterations = config_service.get_int(
            db, "MAX_FUNCTION_CALL_ITERATIONS", DEFAULT_MAX_ITERATIONS
        )
        for iteration in range(max_iterations):
            response = client.chat_completion(
                messages=llm_messages,
                tools=tools if tools else None,
            )

            total_tokens += response.get("tokens_used", 0)
            final_model = response.get("model_used")

            tool_calls = response.get("tool_calls") or []

            if not tool_calls:
                final_content = response.get("content") or _get_prompt(
                    db, "NO_RESPONSE", "I'm not sure how to respond."
                )

                conversation_service.add_message(
                    db,
                    conv.id,
                    role="assistant",
                    content=final_content,
                    tokens_used=total_tokens,
                    model_used=final_model,
                )

                if is_new_conversation:
                    try:
                        title = client.generate_conversation_title(user_message)
                        conversation_service.set_title_if_empty(db, conv.id, title)
                    except Exception:
                        conversation_service.set_title_if_empty(
                            db, conv.id, user_message[:60]
                        )

                return {
                    "conversation_id": conv.id,
                    "message": final_content,
                    "function_calls": function_calls_log,
                    "is_new_conversation": is_new_conversation,
                    "tokens_used": total_tokens,
                    "model_used": final_model,
                }

            llm_messages.append(
                {
                    "role": "assistant",
                    "content": response.get("content"),
                    "tool_calls": tool_calls,
                }
            )

            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                fn_args_raw = tc.get("function", {}).get("arguments", "{}")
                tc_id = tc.get("id", "")

                try:
                    if isinstance(fn_args_raw, str):
                        fn_args = json.loads(fn_args_raw) if fn_args_raw.strip() else {}
                    elif isinstance(fn_args_raw, dict):
                        fn_args = fn_args_raw
                    else:
                        fn_args = {}
                except json.JSONDecodeError:
                    fn_args = {}

                if not isinstance(fn_args, dict):
                    fn_args = {}

                for key, val in fn_args.items():
                    if isinstance(val, str):

                        if val.lower() in ("true", "false"):
                            fn_args[key] = val.lower() == "true"

                        else:
                            try:
                                fn_args[key] = int(val)
                            except ValueError:
                                try:
                                    fn_args[key] = float(val)
                                except ValueError:
                                    pass

                logger.info(f"LLM calling function: {fn_name} with args {fn_args}")

                result = functions.execute_function(fn_name, fn_args, db, user)
                function_calls_log.append(
                    {
                        "name": fn_name,
                        "args": fn_args,
                        "result": result,
                    }
                )

                conversation_service.add_message(
                    db,
                    conv.id,
                    role="function",
                    content=None,
                    function_name=fn_name,
                    function_result=result,
                )

                llm_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "name": fn_name,
                        "content": json.dumps(result, default=str),
                    }
                )

        fallback_msg = _get_prompt(
            db, "LOOP_LIMIT", "I got stuck in a loop. Please try rephrasing."
        )
        conversation_service.add_message(
            db, conv.id, role="assistant", content=fallback_msg
        )
        return {
            "conversation_id": conv.id,
            "message": fallback_msg,
            "function_calls": function_calls_log,
            "is_new_conversation": is_new_conversation,
            "tokens_used": total_tokens,
            "model_used": final_model,
        }

    except LLMNotConfiguredError:
        return {
            "error": True,
            "message": _get_prompt(db, "NOT_CONFIGURED", "AI is not configured."),
        }
    except LLMError as e:
        logger.error(f"LLM error during chat: {e}")

        error_str = str(e).lower()
        if "429" in error_str or "rate_limit" in error_str or "rate limit" in error_str:
            wait_msg = _get_prompt(
                db,
                "LLM_RATE_LIMITED",
                "The AI service is temporarily rate-limited. "
                "Please try again in a few minutes, or contact your admin to switch models.",
            )
            return {"error": True, "message": wait_msg}

        if "401" in error_str or "invalid_api_key" in error_str:
            return {
                "error": True,
                "message": _get_prompt(
                    db,
                    "LLM_INVALID_KEY",
                    "The AI service API key is invalid. Please contact your administrator.",
                ),
            }

        if "timeout" in error_str or "timed out" in error_str:
            return {
                "error": True,
                "message": _get_prompt(
                    db,
                    "LLM_TIMEOUT",
                    "The AI is taking too long to respond. Please try again.",
                ),
            }

        return {
            "error": True,
            "message": _get_prompt(
                db,
                "ERROR_FALLBACK",
                "Sorry, I encountered an error. Please try again.",
            ),
        }
    except Exception as e:
        logger.error(f"Unexpected chat error: {type(e).__name__}: {e}", exc_info=True)
        return {
            "error": True,
            "message": _get_prompt(
                db,
                "ERROR_FALLBACK",
                "Sorry, I encountered an error. Please try again.",
            ),
        }
