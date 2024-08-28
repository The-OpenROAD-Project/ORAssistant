from flask import Flask, request, Response
import requests
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

ORASSISTANT_ENDPOINT = os.getenv('ORASSISTANT_ENDPOINT')

@app.route('/api/chat', methods=['POST'])
def proxy():
    try:
        print(request.json)
        # Forward the request to the ORASSISTANT endpoint
        response = requests.post(ORASSISTANT_ENDPOINT, json=request.json)
        
        # Return the response from the ORASSISTANT endpoint
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers['content-type']
        )
    except requests.RequestException as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True, port=3001)