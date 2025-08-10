# 🚀 Enhanced YouTube Niche Finder

A simple Streamlit web app to find high-demand YouTube niches.

## Features
- Demand Score (Views / Subscribers)
- Engagement % (Likes + Comments) / Views
- Filter by recent uploads
- Keyword suggestions from YouTube autocomplete
- Export results to CSV

## Setup
1. Create a YouTube Data API key from https://console.cloud.google.com/.
2. Upload these files to a GitHub repo.
3. Go to https://share.streamlit.io/ -> Deploy app.
4. In Streamlit settings, set an environment variable:

   API_KEY=your_youtube_api_key_here

## Run Locally
```bash
pip install -r requirements.txt
streamlit run niche_finder.py
```
