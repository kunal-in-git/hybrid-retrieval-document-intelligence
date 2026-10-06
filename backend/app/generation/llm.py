import os

import ollama


OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

GENERATION_MODEL = os.getenv(
    "GENERATION_MODEL",
    "llama3.1:8b",
)

client = ollama.Client(host=OLLAMA_HOST)


def generate_answer(
    query: str,
    contexts: list[dict],
) -> str:

    if not contexts:
        return (
            "I could not find relevant information "
            "in the provided documents."
        )

    context_parts = []

    for index, context in enumerate(contexts, start=1):

        context_parts.append(
            f"""
[Context {index}]

Page: {context.get("page")}
Section: {context.get("section")}

Relevant passage:
{context.get("matched_child_text", "")}

Surrounding context:
{context.get("parent_text", "")}
""".strip()
        )

    context_text = "\n\n".join(context_parts)

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the provided document context.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. If the answer cannot be found in the provided context,
   clearly say that it was not found.
4. Prefer the relevant passage when answering.
5. Use the surrounding context to understand the relevant passage.
6. Cite supporting claims using [1], [2], [3], etc.
7. The citation number must correspond exactly to the Context number.
8. Only cite a context when it supports the claim.
9. Do not write "Supporting claim:".
10. Do not write "[Context 1]", "[Context 2]", etc. in the answer.
11. Keep the answer concise and factual.

User question:
{query}

Document context:

{context_text}
"""

    response = client.chat(
        model=GENERATION_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"]