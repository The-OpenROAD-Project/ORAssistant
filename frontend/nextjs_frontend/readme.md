# NextJS Frontend for ORAssistant

This project is a NextJS frontend for the ORAssistant application.

## Setup Instructions

1. Set up Next.js project:
   ```
   npx create-next-app@latest nextjs-project
   cd orassistant-frontend
   ```

2. Install required packages:
   ```
   npm install axios @google/generative-ai
   ```

3. Set up environment variables:
   - Copy the `.env_example` file to `.env`
   - Fill in the following variables in the `.env` file:
     ```
     ORASSISTANT_ENDPOINT=<your_orassistant_endpoint>
     GEMINI_API_KEY=<your_gemini_api_key>
     ```

4. Start the Python API proxy:
   - Ensure you have Flask and required packages installed:
     ```
     pip install flask requests flask-cors python-dotenv
     ```
   - Run the API proxy:
     ```
     python apiproxy.py
     ```

5. Start the Next.js development server:
   ```
   npm run dev
   ```

Your NextJS frontend should now be running and connected to the ORAssistant backend through the API proxy. The Gemini API key will be used for generating suggested questions in the frontend.

## Additional Notes

- Make sure the ORASSISTANT_ENDPOINT in your `.env` file points to the correct backend endpoint.
- The API proxy runs on port 3001 by default. Ensure this port is available or modify the port in `apiproxy.py` if needed.
- The Next.js development server typically runs on `http://localhost:3000`. You can access your application at this address.
