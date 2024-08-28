# OpenROAD GitHub Discussions Analysis

This Streamlit application provides an interactive visualization and analysis of OpenROAD GitHub Discussions.

## Features

- **Data Loading**: Fetches the latest data from the Hugging Face dataset repository.
- **Interactive Filters**: Users can filter discussions by category, tool, and date range.
- **Visualizations**: 
  - Pie chart for discussion categories
  - Line chart for weekly discussion trends
  - Bar charts for tool distribution and top active authors
  - Word cloud of common terms in discussion titles
- **Detailed View**: Users can select and view details of individual discussions.
- **Data Export**: Option to download filtered data as a CSV file.

## How to Run

1. Ensure you have the required libraries installed:
   ```
   pip install streamlit pandas plotly wordcloud matplotlib requests
   ```

2. Run the Streamlit app:
   ```
   streamlit run analysis/steam.py
   ```

3. The app will open in your default web browser.

## Data Source

The data is sourced from the [OpenROAD_Discussions dataset](https://huggingface.co/datasets/procodec/OpenROAD_Discussions) on Hugging Face. The application automatically fetches the latest version of the dataset.

## Note

Please check the Hugging Face repository for any updates to the dataset URL. If there's a newer release, update the `url` variable in the `load_data()` function in `analysis/analysis.py`.


