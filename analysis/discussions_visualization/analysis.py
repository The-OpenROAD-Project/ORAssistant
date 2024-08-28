import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json
from datetime import datetime, timezone
import requests

# Set page config at the very beginning
st.set_page_config(page_title="OpenROAD GitHub Discussions Analysis", layout="wide")

# Load and process data
@st.cache_data
def load_data():
    # Get the latest file information from the Hugging Face API
    api_url = "https://huggingface.co/api/datasets/procodec/OpenROAD_Discussions/tree/main"
    response = requests.get(api_url)
    files = response.json()
    
    # Find the latest .txt file (assuming it's the data file)
    latest_file = max((f for f in files if f['path'].endswith('.txt')), key=lambda x: x['lastCommit']['date'])
    
    # Construct the download URL for the latest file
    download_url = f"https://huggingface.co/datasets/procodec/OpenROAD_Discussions/resolve/main/{latest_file['path']}?download=true"
    
    # Download and process the data
    response = requests.get(download_url)
    data = [json.loads(line) for line in response.text.splitlines()]
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%dT%H:%M:%SZ', utc=True)
    return df

# Load data
df = load_data()

st.title("OpenROAD GitHub Discussions Analysis")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    category_filter = st.multiselect("Categories", df['category'].unique())
    tool_filter = st.multiselect("Tools", df['Tool'].unique())
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    date_range = st.date_input("Date Range", [min_date, max_date])

# Convert date_range to UTC timezone
date_range_utc = [
    datetime.combine(date_range[0], datetime.min.time()).replace(tzinfo=timezone.utc),
    datetime.combine(date_range[1], datetime.max.time()).replace(tzinfo=timezone.utc)
]

# Apply filters
mask = df['date'].between(date_range_utc[0], date_range_utc[1]) & \
       (df['category'].isin(category_filter) if category_filter else True) & \
       (df['Tool'].isin(tool_filter) if tool_filter else True)
filtered_df = df[mask]

# Overview metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Discussions", len(filtered_df))
col2.metric("Categories", len(filtered_df['category'].unique()))
col3.metric("Tools", len(filtered_df['Tool'].unique()))
col4.metric("Authors", len(filtered_df['author'].unique()))

# Main content
col1, col2 = st.columns(2)

with col1:
    # Category distribution
    fig_category = px.pie(filtered_df, names='category', title="Discussion Categories")
    st.plotly_chart(fig_category, use_container_width=True)
    
    # Timeline of discussions
    timeline_data = filtered_df.groupby(filtered_df['date'].dt.to_period('W')).size().reset_index(name='count')
    timeline_data['date'] = timeline_data['date'].dt.to_timestamp()
    fig_timeline = px.line(timeline_data, x='date', y='count', title="Weekly Discussions")
    st.plotly_chart(fig_timeline, use_container_width=True)

with col2:
    # Tool distribution
    tool_counts = filtered_df['Tool'].value_counts()
    fig_tool = px.bar(x=tool_counts.index, y=tool_counts.values, title="Discussions by Tool")
    st.plotly_chart(fig_tool, use_container_width=True)
    
    # Author activity
    author_counts = filtered_df['author'].value_counts().head(10)
    fig_author = px.bar(x=author_counts.index, y=author_counts.values, title="Top 10 Active Authors")
    st.plotly_chart(fig_author, use_container_width=True)

# Word cloud
st.subheader("Common Terms in Discussion Titles")
text = ' '.join(filtered_df['title'])
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
fig, ax = plt.subplots()
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis('off')
st.pyplot(fig)

# Detailed discussion view
st.header("Discussion Details")
selected_discussion = st.selectbox("Select a discussion:", filtered_df['title'])
if selected_discussion:
    discussion = filtered_df[filtered_df['title'] == selected_discussion].iloc[0]
    st.subheader(f"Discussion: {discussion['title']}")
    st.write(f"**ID:** {discussion['id']} | **Author:** {discussion['author']} | **Date:** {discussion['date']}")
    st.write(f"**Category:** {discussion['category']} | **Subcategory:** {discussion['subcategory']} | **Tool:** {discussion['Tool']}")
    st.write(f"**URL:** {discussion['url']}")
    with st.expander("Description"):
        st.write(discussion['description'])
    with st.expander("Conversation"):
        for msg in discussion['content']:
            st.text(f"{msg['author']} ({msg['date']}):")
            st.write(msg['message'])
            st.markdown("---")

# Download filtered data
st.download_button("Download Filtered Data", filtered_df.to_csv(index=False), "filtered_discussions.csv", "text/csv")