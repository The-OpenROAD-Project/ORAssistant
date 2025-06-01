from flask import Flask, request, Response
import requests
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

BACKEND_ENDPOINT = os.getenv('BACKEND_ENDPOINT')

@app.route('/api/chat', methods=['POST']) 
def proxy():
    try:
        app.logger.info('Received request: %s', request.json)
        
        response = requests.post(BACKEND_ENDPOINT, 
                               json=request.json)
        
        app.logger.info('Response status: %s', response.status_code)
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers['content-type']
        )
    except requests.RequestException as e:
        app.logger.error('Request failed: %s', str(e))
        return {'error': str(e)}, 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    app.run(debug=False, port=port)
