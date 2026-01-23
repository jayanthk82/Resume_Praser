from typing import  Any

def chat_with_reasoning_followup(client: Any,initial_prompt: str,follow_up_prompt: str,model: str = "xiaomi/mimo-v2-flash:free") -> Any:

    # 1. First API call
    response1 = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": initial_prompt}
        ],
        extra_body={"reasoning": {"enabled": True}}
    )

    # Extract the assistant message
    assistant_msg = response1.choices[0].message

    # 2. Construct history preserving reasoning_details
    # Note: We must explicitly pass 'reasoning_details' back if the API supports it
    messages = [
        {"role": "user", "content": initial_prompt},
        {
            "role": "assistant",
            "content": assistant_msg.content,
            "reasoning_details": getattr(assistant_msg, "reasoning_details", None)
        },
        {"role": "user", "content": follow_up_prompt}
    ]

    # 3. Second API call with context
    response2 = client.chat.completions.create(
        model=model,
        messages=messages,
        extra_body={"reasoning": {"enabled": True}}
    )

    return response2.choices[0].message
