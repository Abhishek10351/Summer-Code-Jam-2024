import json
import os

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

convo_template = """Give me 10 lines of conversation between 3 people (userid's 0-2) who are in a debate amongst each
other, make the conversation seem modern like a typical discord chat, they are discussing on the topic "{topic}".

Using this JSON schema:
    Message = {{"userid": int, "message": str}}
Return a `list[Message]`
"""


summary_template = """Summarize the conversation below:
```
{text}
```
"""


class Gemini:
    """Gemini API Client."""

    def __init__(self) -> None:
        """Initialize Gemini API Client."""
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }
        self.finish_errors = {
            "MAX_TOKENS": "The maximum number of tokens as specified in the request was reached.",
            "SAFETY": "The content was blocked for safety reasons.",
            "RECITATION": "The content was flagged for recitation reasons.",
            "LANGUAGE": "You are using a language that is not supported.",
            "OTHER": "There was an error for Unknown reason.",
        }

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"},
            safety_settings=self.safety_settings,
        )

    async def generate_conversation(self, prompt: str) -> str:
        """Generate a conversation based on the given topic."""
        response = await self.model.generate_content_async(
            convo_template.format(topic=prompt)
        )

        return await self.verify(response)

    async def summarize_conversation(self, text: str) -> str:
        """Summarize the conversation."""
        response = await self.model.generate_content_async(
            summary_template.format(text=text)
        )
        return await self.verify(response)

    async def verify(self, response) -> str:
        """Verify the content of the output and return a valid response."""
        if response.prompt_feedback.block_reason:
            reason = response.prompt_feedback.block_reason.name
            if reason == "SAFETY":
                message = "Your request was blocked because of safety reasons."
                return (
                    '{"summary": "Your request was blocked because of safety reasons."}'
                )
            else:
                message = "Your request was blocked because of other reasons."
                return (
                    '{"summary": "Your request was blocked because of other reasons."}'
                )
        elif response.candidates[0].finish_reason not in [
            "STOP",
            "FINISH_REASON_UNSPECIFIED",
        ]:

            try:
                return response.text
            except Exception as e:
                print(e)
            data = self.finish_errors.get(
                response.candidates[0].finish_reason.name, "Unknown error."
            )
            return json.dumps({"summary": f"{data}"})

        else:
            try:
                return response.text
            except Exception as e:
                print(e)
                return '{"summary": "Please provide a valid conversation."}'


gemini_client = Gemini()
