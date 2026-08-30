from google import genai

from app.config import GEMINI_API_KEY, MODEL_NAME


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_response(prompt: str) -> str:

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt
    )

    return interaction.output_text