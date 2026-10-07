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

SYSTEM_PROMPT = """You answer questions using ONLY the numbered sources the user provides.

Rules:
- Every sentence that states a fact must end with the number of the source that supports it, in square brackets, like [1] or [2].
- Only use numbers of sources that were provided.
- Do not use outside knowledge.
- If the sources answer the question fully or partly, give that answer. The source text may contain formatting noise from PDF extraction; read past it.
- Only if no source is relevant, say: "I could not find this in the documents."
- Keep the answer concise.

Example of the required format:
The study title must appear on the title page [1]. The sponsor's name is also required [1][3]."""


def build_context_text(
    contexts: list[dict],
) -> str:
    """
    Number each parent context so the model can cite it.

    The number shown here ([1], [2], ...) is exactly the
    citation format we ask the model to use, and it maps
    to contexts[number - 1] in the API response.
    """

    parts = []

    for index, context in enumerate(contexts, start=1):
        parts.append(
            f"[{index}] {context.get('filename')}, "
            f"page {context.get('page')}, "
            f"section: {context.get('section')}\n"
            f"{context.get('parent_text', '')}"
        )

    return "\n\n".join(parts)


def generate_answer(
    query: str,
    contexts: list[dict],
) -> str:

    if not contexts:
        return (
            "I could not find relevant information "
            "in the provided documents."
        )

    context_text = build_context_text(contexts)

    response = client.chat(
        model=GENERATION_MODEL,
        options={
            "temperature": 0,
        },
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Sources:\n\n{context_text}\n\n"
                    f"Question: {query}"
                ),
            },
        ],
    )

    return response["message"]["content"]
