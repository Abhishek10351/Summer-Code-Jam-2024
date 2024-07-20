import json
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

convo_template = """Give me 10 lines of conversation between 3 people (userid's 0-2) who are in a debate amongst each
other, make the conversation seem modern like a typical discord chat, they are discussing on the topic "{topic}".

Using this JSON schema:
    Message = {{"userid": int, "message": str}}
Return a `list[Message]`
"""


class Gemini:
    """Gemini API Client."""

    def __init__(self) -> None:
        """Initialize Gemini API Client."""
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"},
        )

    async def generate_conversation(self, prompt: str) -> str:
        """Generate a conversation based on the given topic."""
        response = await self.model.generate_content_async(convo_template.format(topic=prompt))
        json_output = response.text.lstrip("```json").rstrip("```").strip()
        return json.loads(json_output)


gemini_client = Gemini()
