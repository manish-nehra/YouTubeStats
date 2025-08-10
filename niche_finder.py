import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# === CONFIG ===
API_KEY = os.getenv("API_KEY")  # From Streamlit Cloud Environment Variables
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_keyword_suggestions(query):
    """Fetch keyword suggestions from YouTube Autocomplete API."""
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}"
    response = requests.get(url)
    if response.status_code == 200:
        suggestions = response.json()[1]
        return suggestions
    return []

def youtube_search(keyword, max_results=10, recent_days=None):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

    search_response = youtube.search().list(
        q=keyword,
        type="video",
        order="viewCount",
        part="id,snippet",
        maxResults=max_results
    ).execute()

    results = []
    cutoff_date = None
    if recent_days:
        cutoff_date = datetime.utcnow() - timedelta(days=recent_days)

    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel_title = item["snippet"]["channelTitle"]
        published_at = item["snippet"]["publishedAt"]

        # Skip if filtering recent uploads
        if cutoff_date:
            video_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            if video_date < cutoff_date:
                continue

        video_response = youtube.videos().list(
            part="statistics,snippet",
            id=video_id
        ).execute()

        stats = video_response["items"][0]["statistics"]
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0)) if "likeCount" in stats else 0
        comments = int(stats.get("commentCount", 0)) if "commentCount" in stats else 0

        engagement_score = round(((likes + comments) / views) * 100, 2) if views > 0 else 0

        channel_id = video_response["items"][0]["snippet"]["channelId"]
        channel_response = youtube.channels().list(
            part="statistics",
            id=channel_id
        ).execute()

        subs = int(channel_response["items"][0]["statistics"].get("subscriberCount", 0))
        demand_score = round(views / (subs + 1), 2)

        results.append({
            "Video Title": title,
            "Channel": channel_title,
            "Views": views,
            "Subscribers": subs,
            "Demand Score": demand_score,
            "Engagement %": engagement_score,
            "Published At": published_at
        })

    results.sort(key=lambda x: x["Demand Score"], reverse=True)
    return results

# === Streamlit UI ===
st.set_page_config(page_title="YouTube Niche Finder", layout="wide")
st.title("🚀 Enhanced YouTube Niche Finder")
st.write("Analyze video niches with demand, engagement, and competition data.")

keyword = st.text_input("Keyword:", "")
max_results = st.slider("Number of results:", 5, 50, 10)
recent_days = st.slider("Only show videos uploaded in the last X days (0 = no filter):", 0, 90, 0)

if keyword.strip():
    st.subheader("💡 Suggested Keywords")
    suggestions = get_keyword_suggestions(keyword)
    st.write(", ".join(suggestions))

if st.button("Find Niche"):
    if not API_KEY:
        st.error("API Key not set! Please set API_KEY in Streamlit Cloud settings.")
    elif keyword.strip() == "":
        st.warning("Please enter a keyword.")
    else:
        with st.spinner("Fetching data..."):
            data = youtube_search(keyword, max_results, recent_days if recent_days > 0 else None)
            df = pd.DataFrame(data)
            if df.empty:
                st.warning("No videos found for this filter.")
            else:
                st.success("Analysis complete!")
                st.dataframe(df)

                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv, f"{keyword}_niche_analysis.csv", "text/csv")
