import requests
from chainforge.providers import provider

# Constants
ORASSISTANT_ENDPOINT = ""
LIST_ALL_ENDPOINT = f"{ORASSISTANT_ENDPOINT}/chains/listAll"

# Retrieve available endpoints from the /chains/listAll endpoint
def get_available_endpoints():
    try:
        response = requests.get(LIST_ALL_ENDPOINT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error retrieving endpoints: {str(e)}")
        return ["error"]  # fallback default endpoints

# Fetch the endpoints dynamically
available_endpoints = get_available_endpoints()

# Function to extract retriever types from endpoints
def get_retriever_types(endpoints):
    return list(set([endpoint.split('/')[2] for endpoint in endpoints if len(endpoint.split('/')) > 2]))

# Get retriever types
retriever_types = get_retriever_types(available_endpoints)

CUSTOM_PROVIDER_SETTINGS_SCHEMA = {
    "settings": {
        "endpoint": {
            "type": "string",
            "title": "Endpoint",
            "description": "Select the endpoint to use.",
            "enum": available_endpoints,
            "default": available_endpoints[0] if available_endpoints else "",
        },
        "retriever": {
            "type": "string",
            "title": "Retriever Type",
            "description": "Select the retriever type to use.",
            "enum": retriever_types,
            "default": retriever_types[0] if retriever_types else "",
        },
        "listSources": {
            "type": "boolean",
            "title": "List Sources",
            "description": "Whether to list sources in response or not.",
            "default": False,
        },
        "listContext": {
            "type": "boolean",
            "title": "List Context",
            "description": "Whether to list context in response or not.",
            "default": False,
        }
    },
    "ui": {
        "endpoint": {
            "ui:widget": "select"
        },
        "retriever": {
            "ui:widget": "select"
        },
        "listSources": {
            "ui:widget": "checkbox"
        },
        "listContext": {
            "ui:widget": "checkbox"
        }
    }
}

@provider(name="OR Assistant",
          emoji="🌐",
          models=['default-model'],
          rate_limit="sequential",
          settings_schema=CUSTOM_PROVIDER_SETTINGS_SCHEMA)
          
def CustomEndpointCompletion(prompt: str, endpoint: str, retriever: str, listSources: bool = True, listContext: bool = True, **kwargs) -> str:
    # Preparing the payload
    payload = {
        "query": prompt,
        "endpoint": endpoint,
        "retriever": retriever,
        "list_sources": listSources,
        "list_context": listContext
    }

    # Making a request to the proxy cache server
    try:
        response = requests.post(ORASSISTANT_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        response_text = data.get('response', '')

        # Extract the sources list
        sources = data.get('sources', [])
        if not isinstance(sources, list):
            return "Error parsing the API response: sources is not a list"

        # Convert sources to a formatted string with each source on a new line
        formatted_sources = "\n".join(sources)

        # Combine the response and formatted sources
        combined_response_sources = response_text + "" + formatted_sources
        return combined_response_sources
    except requests.RequestException as e:
        return f"Error communicating with the API: {str(e)}"
    except (ValueError, KeyError) as e:
        return f"Error parsing the API response: {str(e)}"