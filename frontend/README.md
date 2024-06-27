# FrontEnd For Streamlit

This Folder contains the frontend code for the OR Assistant using Streamlit. Follow the instructions below to set up the environment, run the application, and perform testing using a mock API.

## Preparing the Environment Variables

To configure the application, you'll need to set up the following environment variables in your `.env` file:

```
CHAT_ENDPOINT=<your-chat-endpoint> Defaults to http://localhost:8000/chatApp
```

## For Feedback Evaluation (Optional)

To collect feedback, you need to set up a Google Sheet and configure the necessary environment variables:

1. **Create a Google Sheet**:
   - Give edit access to the sheet to the service account email.
   - Add the sheet ID in the environment variable.

    ```plaintext
    FEEDBACK_SHEET_ID=your-google-sheet-id
    ```

2. **Using Another Worksheet Inside the Google Sheet**:
   - If you are using another worksheet inside the Google Sheet, enter the GID as well.

    ```plaintext
    FEEDBACK_SHEET_GID=your-gid
    ```

3. **Set Up Google Cloud Console**:
   - Open Google Cloud Console, enable the Sheets API, and create a service account.
   - Give access to this service account email.
   - Export credentials as JSON and add its path in the environment variable.

    ```plaintext
    GOOGLE_CREDENTIALS_JSON=<path-to-your-google-credentials-json>
    ```
4. **Set the Current Version for Feedback Evaluation:**
   - Add the current version of the feedback evaluation to the environment variables.
    
    ```plaintext
    RAG_VERSION=<current-version>
    ```
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

This project is licensed under the GNU GENERAL PUBLIC LICENSE - see the [LICENSE](../../LICENSE) file for details.