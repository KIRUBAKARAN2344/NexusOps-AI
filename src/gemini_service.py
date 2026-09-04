import os
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def get_structured_recommendation(self, prompt: str, system_instruction: str) -> str:
        """Calls Gemini API and asks for JSON output based on prompt."""
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not set.")
            
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.2, # Keep it highly deterministic and grounded
            ),
        )
        return response.text
