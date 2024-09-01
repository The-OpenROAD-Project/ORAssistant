from chainforge.providers import provider
import requests

# Constants
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
HEADERS = {
    'Content-Type': 'application/json',
}

CUSTOM_PROVIDER_SETTINGS_SCHEMA = {
    "settings": {
        "api_key": {
            "type": "string",
            "title": "API Key",
            "description": "Enter your Gemini 1.5 Pro API key.",
            "default": "",
        },
    },
    "ui": {
        "api_key": {
            "ui:widget": "password"
        },
    }
}

@provider(name="Gemini 1.5 Pro",
          emoji="🔮",
          models=['gemini-1.5-pro'],
          rate_limit="sequential",
          settings_schema=CUSTOM_PROVIDER_SETTINGS_SCHEMA)
def Gemini15ProCompletion(prompt: str, api_key: str, **kwargs) -> str:
    # Preparing the payload
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0
        }
    }
    
    # Params for the request
    params = {
        "key": api_key
    }
    
    # Making a request to your custom API endpoint
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error communicating with the API: {str(e)}"
    
    # Handling the API response
    try:
        data = response.json()
        # Assuming the API returns a field named 'content' inside 'candidates'
        candidates = data.get('candidates', [])
        if not candidates or 'content' not in candidates[0] or 'parts' not in candidates[0]['content']:
            return "0.51"

        content_parts = candidates[0]['content']['parts']
        combined_text = " ".join([part['text'] for part in content_parts if 'text' in part])
        return combined_text

    except (ValueError, KeyError) as e:
        return f"Error parsing the API response: {str(e)}"