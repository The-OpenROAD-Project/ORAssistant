# OR Assistant: Populating Human Evaluation Form

This project helps populate a Google Form for human evaluation based on questions and generated answers in a Google Sheet.

## Setup Guide

### Automatic Sheet & Form Creation

1. **Setup Google Cloud Service Account**:
   - Open Google Cloud Console, enable the Sheets API, Form API, Drive API and create a service account.
   - Give access to this service account email.
   - Export credentials as JSON and add its path in the environment variable.

    ```plaintext
    GOOGLE_CREDENTIALS_JSON=<path-to-your-google-credentials-json>
    ```

2. **Run the Setup Script**:
    - Execute the setup script to create Google Sheets and Forms automatically based on your needs:
    ```sh
    python setup.py
    ```
    - You will be prompted:
        ```plaintext
        Do you want to create a Google Form? [y/n]:
        ```
        Choose `y` or `n` according to your needs.
    - Another prompt will ask:
        ```plaintext
        Do you want to create a Google Sheet with columns [Questions, Generated Answers]? [y/n]:
        ```
        Choose `y` or `n` as required.
    - Provide your email address to give it edit access to the file:
        ```plaintext
        Enter your email address to share the created resources with:
        ```
    - The script will automatically update the `.env` file with the sheet ID and form ID.


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

5. **Setup Google Cloud Service Account [Mentioned in Automatic Sheet & Form Creation](#automatic-sheet-form-creation):**
   - Open Google Cloud Console, enable the Sheets API, Form API, Drive API and create a service account.
   - Give access to this service account email.
   - Export credentials as JSON and add its path in the environment variable.

    ```plaintext
    GOOGLE_CREDENTIALS_JSON=<path-to-your-google-credentials-json>
    ```
6. **Run the Streamlit Application**:
    ```sh
    streamlit run main.py
    ```
    
### License

This project is licensed under the GNU GENERAL PUBLIC LICENSE - see the [LICENSE](../../LICENSE) file for details.
