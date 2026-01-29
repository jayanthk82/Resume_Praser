from typing import Any
from config import Config 
from openai import OpenAI #type: ignore

def chat_with_reasoning_followup(
    client, 
    initial_prompt: str, 
    follow_up_prompt: str, 
    model: str = "arcee-ai/trinity-large-preview:free"
) -> Any:
    """
    Executes a two-turn conversation while preserving reasoning tokens 
    to maintain context and logical consistency.
    """
    
    # 1. Initial Request
    # We enable reasoning via the extra_body parameter
    response1 = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": initial_prompt}],
        extra_body={"reasoning": {"enabled": True}}
    )

    assistant_msg = response1.choices[0].message

    # 2. Construct Message History
    # We include 'reasoning_details' in the assistant turn to preserve the logic flow
    messages = [
        {"role": "user", "content": initial_prompt},
        {
            "role": "assistant",
            "content": assistant_msg.content,
            "reasoning_details": getattr(assistant_msg, "reasoning_details", None)
        },
        {"role": "user", "content": follow_up_prompt}
    ]

    # 3. Follow-up Request
    # The model now sees its previous reasoning chain
    response2 = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={"reasoning": {"enabled": True}}
    )

    return response2.choices[0].message





