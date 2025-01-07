from typing import Dict, List, Optional, Tuple
from groq import Groq
from duckduckgo_search import DDGS
import logging
from ..models.data_models import UserPreferences

class CourseRecommender:
    def __init__(self, api_key: str):
        self.groq_client = Groq(api_key=api_key)

    def generate_recommendations(self, preferences: UserPreferences) -> Tuple[str, Optional[List[Dict]]]:
        try:
            prompt = self._create_prompt(preferences)
            response = self._get_ai_response(prompt)
            search_results = self._get_additional_resources(preferences.subject)
            return response, search_results
        except Exception as e:
            logging.error(f"Error generating recommendations: {str(e)}")
            return str(e), None

    def _create_prompt(self, preferences: UserPreferences) -> str:
        return f"""As a course recommendation expert, suggest 3-5 specific courses for someone with these preferences:
        - Name: {preferences.name}
        - Subject: {preferences.subject}
        - Time available: {preferences.availability}
        - Budget: ${preferences.budget}
        - Preferred format: {preferences.format}
        - Experience level: {preferences.experience}
        - Learning goal: {preferences.goal}

        For each course, include:
        1. Course title and platform
        2. Price and duration
        3. Key features
        4. Why it matches their preferences
        5.link to redirect to the course
        
        Format the response in clear, readable markdown."""

    def _get_ai_response(self, prompt: str) -> str:
        response = self.groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful course recommendation assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content

    def _get_additional_resources(self, subject: str) -> List[Dict]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    f"learn {subject} course tutorial guide",
                    max_results=5
                ))
            return results
        except Exception as e:
            logging.error(f"Error fetching additional resources: {str(e)}")
            return [] 