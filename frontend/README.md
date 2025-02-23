# Frontend For Streamlit

This folder contains the frontend code for the OR Assistant using Streamlit. Follow the instructions below to set up the environment, run the application, and perform testing using a mock API.

## Preparing the Environment Variables

To configure the application, you'll need to set up the following environment variables in your `.env` file:

```
CHAT_ENDPOINT=<your-chat-endpoint> Defaults to http://localhost:8000/chatApp
```

## For Feedback Evaluation (Optional)

TODO!

## Running the Application

### Install Required Packages

Ensure you have the necessary dependencies installed by running:

```bash
pip install -r requirements.txt
```

### Run the Streamlit Application

Start the Streamlit application by running:

```bash
streamlit run streamlit_app.py
```

## Testing Using Mock API

To test your application using a mock API, you can run the provided mock endpoint script:

```bash
python utils/mock_endpoint.py
```

This will start a mock API server that simulates responses for testing purposes.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE - see the [LICENSE](../LICENSE) file for details.