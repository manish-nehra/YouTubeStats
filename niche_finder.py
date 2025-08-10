import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build

API_KEY = os.getenv("API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

SNAPSHOT_FILE = "data/snapshots.csv"

st.set_page_config(page_title="Niche Finder Pro", layout="wide")

tab1, tab2 = st.tabs(["🔍 Niche Finder", "📈 Channel Growth Finder"])

# ------------------- TAB 1: NICHE FINDER -------------------
with tab1:
    st.header("YouTube Niche Finder")
    keyword = st.text_input("Enter keyword:")
    max_results = st.slider("Max results", 5, 50, 10)

    if st.button("Find Niches"):
        if not keyword:
            st.warning("Please enter a keyword")
        else:
            request = youtube.search().list(
                q=keyword,
                part="snippet",
                type="channel",
                maxResults=max_results
            )
            response = request.execute()

            results = []
            for item in response.get("items", []):
                channel_id = item["snippet"]["channelId"]
                channel_title = item["snippet"]["title"]
                stats_req = youtube.channels().list(
                    part="statistics",
                    id=channel_id
                ).execute()
                stats = stats_req["items"][0]["statistics"]
                subs = int(stats.get("subscriberCount", 0))
                views = int(stats.get("viewCount", 0))
                videos = int(stats.get("videoCount", 0))

                results.append({
                    "Channel": channel_title,
                    "Channel ID": channel_id,
                    "Subscribers": subs,
                    "Views": views,
                    "Videos": videos
                })

                # Save snapshot for growth tracking
                snapshot = pd.DataFrame([{
                    "date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "subscribers": subs,
                    "views": views,
                    "videos": videos
                }])
                if os.path.exists(SNAPSHOT_FILE):
                    old_df = pd.read_csv(SNAPSHOT_FILE)
                    new_df = pd.concat([old_df, snapshot], ignore_index=True)
                    new_df.to_csv(SNAPSHOT_FILE, index=False)
                else:
                    snapshot.to_csv(SNAPSHOT_FILE, index=False)

            df = pd.DataFrame(results)
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False), "niche_results.csv")

# ------------------- TAB 2: CHANNEL GROWTH FINDER -------------------
with tab2:
    st.header("Channel Growth Finder")

    if not os.path.exists(SNAPSHOT_FILE):
        st.info("No snapshot data yet. Run a search in Niche Finder first to build history.")
    else:
        snapshots = pd.read_csv(SNAPSHOT_FILE)
        snapshots["date"] = pd.to_datetime(snapshots["date"])

        min_subs, max_subs = st.slider("Subscriber range", 0, 10_000_000, (0, 1_000_000), step=1000)
        timeframe = st.selectbox("Growth timeframe", ["7d", "30d", "90d"])
        min_videos, max_videos = st.slider("Video count range", 0, 5000, (0, 500))
        min_views = st.number_input("Minimum views in current period", 0, 100_000_000, 0)

        days = int(timeframe.replace("d", ""))
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        latest = snapshots.groupby("channel_id").apply(lambda g: g.sort_values("date").iloc[-1])
        past = snapshots[snapshots["date"] <= cutoff_date].groupby("channel_id").apply(lambda g: g.sort_values("date").iloc[-1])

        growth_data = []
        for cid, row in latest.iterrows():
            if cid in past.index:
                past_row = past.loc[cid]
                sub_growth = row["subscribers"] - past_row["subscribers"]
                view_growth = row["views"] - past_row["views"]
                if (min_subs <= row["subscribers"] <= max_subs and
                    min_videos <= row["videos"] <= max_videos and
                    row["views"] >= min_views):
                    growth_data.append({
                        "Channel": row["channel_title"],
                        "Subscribers": row["subscribers"],
                        "Sub Growth": sub_growth,
                        "Views": row["views"],
                        "View Growth": view_growth,
                        "Videos": row["videos"]
                    })

        growth_df = pd.DataFrame(growth_data).sort_values("Sub Growth", ascending=False)
        st.dataframe(growth_df)
        st.download_button("Download Growth Data", growth_df.to_csv(index=False), "channel_growth.csv")
