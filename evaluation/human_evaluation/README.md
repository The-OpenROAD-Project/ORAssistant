# OR Assistant: Populating Human Evaluation Form

This project helps populate a Google Form for human evaluation based on questions and generated answers in a Google Sheet.

## Setup Guide

### Google Cloud Service Account Setup

1. **Setup Google Cloud Service Account**:
   - Open Google Cloud Console and enable the following APIs:
     - [Google Sheets API](https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com)
     - [Google Drive API](https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com)
     - [Google Forms API](https://console.cloud.google.com/marketplace/product/google/forms.googleapis.com)
   - Create a service account by navigating to the [Service Accounts page](https://console.cloud.google.com/iam-admin/serviceaccounts).
   - Give access to this service account email.
   - Export credentials as JSON and add its path in the environment variable:

    ```plaintext
    GOOGLE_CREDENTIALS_JSON=<path-to-your-google-credentials-json>
    ```

### Automatic Sheet & Form Creation

1. **Run the Setup Script**:

    #### Script Arguments

    - `--create-form`: Create a Google Form.
    - `--create-sheet`: Create a Google Sheet.
    - `--user-email`: Email address to share the created resources with (required).
    - `--form-title`: Title for the Google Form (optional, default is `OR Assistant Feedback Form`).
    - `--sheet-title`: Title for the Google Sheet (optional, default is `OR Assistant Evaluation Sheet`).

    #### Example Usage

    To create both Google Form and Google Sheet with custom titles and share them with a specified email, use the following command:

    ```sh
    python or_assistant.py --create-form --create-sheet --user-email example@domain.com --form-title "Custom Form Title" --sheet-title "Custom Sheet Title"
    ```

### Steps

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/The-OpenROAD-Project/ORAssistant
    cd ORAssistant/evaluation/human_evaluation
    ```

2. **Create a Virtual Environment** (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install Dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Configure Environment Variables**:
    - Copy the example environment variables file:
        ```sh
        cp .env.example .env
        ```
    - Edit the `.env_example` file with your configuration:

    ```plaintext
    # Environment configuration example

    # API endpoint for the chat application
    # (e.g., http://your-api-endpoint.com/chatApp)
    CHAT_ENDPOINT=

    # Google Sheets IDs (Note: These will be filled by setup.py script if you choose to create a new sheet)
    GOOGLE_SHEET_ID=
    
    # (Optional, e.g., A2:A)
    RANGE_QUESTIONS=

    # (Optional, e.g., B2:B)
    RANGE_ANSWERS=

    # Path to the Google Cloud service account credentials JSON file to utilize Sheets API
    # (e.g., /path/to/your/secrets.json)
    GOOGLE_CREDENTIALS_JSON=

    # Google Form ID (Note: This will be filled by setup.py script if you choose to create a new form.)
    GOOGLE_FORM_ID=

    ```

5. **Run the Streamlit Application**:
    ```sh
    streamlit run main.py
    ```
    
### License

This project is licensed under the GNU GENERAL PUBLIC LICENSE - see the [LICENSE](../../LICENSE) file for details.

