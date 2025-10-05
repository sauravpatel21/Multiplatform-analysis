import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import time
from datetime import datetime
from fpdf import FPDF

# Improved backoff strategy with dynamic delay and user-configurable retries
def backoff_strategy(retries=3, initial_delay=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    if e.resp.status in [403, 429]:  # Quota exceeded or rate limit
                        logging.warning(f"Quota error encountered. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        st.error(f"An HTTP error occurred: {e}")
                        raise
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    raise
            st.error("Max retries exceeded. Please try again later.")
            raise Exception("Max retries exceeded. Please try again later.")
        return wrapper
    return decorator

# Fetch channel ID by channel name (with caching)
@st.cache_data(ttl=3600)
def get_channel_id(channel_name, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            part='id',
            q=channel_name,
            type='channel'
        )
        response = request.execute()
        if response['items']:
            return response['items'][0]['id']['channelId']
        else:
            st.warning(f"Channel '{channel_name}' not found.")
            return None
    except Exception as e:
        st.error(f"Failed to fetch channel ID for '{channel_name}': {e}")
        return None

# Fetch channel statistics (with caching)
@st.cache_data(ttl=3600)
def get_channel_stats(channel_id, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.channels().list(
            part='statistics,snippet,contentDetails',
            id=channel_id
        )
        response = request.execute()
        if response['items']:
            channel_info = response['items'][0]
            statistics = channel_info['statistics']
            snippet = channel_info['snippet']
            content_details = channel_info['contentDetails']
            return {
                'Channel_name': snippet['title'],
                'Subscribers': int(statistics['subscriberCount']),
                'Views': int(statistics['viewCount']),
                'Total_videos': int(statistics['videoCount']),
                'playlist_id': content_details['relatedPlaylists']['uploads']
            }
        else:
            st.warning(f"Statistics for channel ID '{channel_id}' not found.")
            return None
    except Exception as e:
        st.error(f"Failed to fetch channel stats for ID '{channel_id}': {e}")
        return None

# Fetch video IDs from a playlist (with caching)
@st.cache_data(ttl=3600)
def get_video_ids(playlist_id, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        video_ids = []
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50
        )
        response = request.execute()
        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        while next_page_token:
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
            next_page_token = response.get('nextPageToken')

        return video_ids
    except Exception as e:
        st.error(f"Failed to fetch video IDs for playlist '{playlist_id}': {e}")
        return []

# Fetch video details (with caching)
@st.cache_data(ttl=3600)
def fetch_video_details(video_ids, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        video_details = []
        for video_id in video_ids:
            request = youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            if response['items']:
                video_info = response['items'][0]
                title = video_info['snippet']['title']
                video_url = f"https://youtube.com/watch?v={video_id}"
                views = video_info['statistics'].get('viewCount', 0)
                likes = video_info['statistics'].get('likeCount', 0)
                comments = video_info['statistics'].get('commentCount', 0)
                duration = video_info['contentDetails']['duration']
                published_at = video_info['snippet']['publishedAt']
                video_details.append({
                    'Title': title,
                    'Views': int(views),
                    'Likes': int(likes),
                    'Comments': int(comments),
                    'Duration': duration,
                    'Published At': published_at,
                    'Video URL': video_url,
                    'Channel': video_info['snippet']['channelTitle']
                })
        return video_details
    except Exception as e:
        st.error(f"Failed to fetch video details: {e}")
        return []

def display_channel_comparison(channel_data):
    try:
        st.subheader("Channel Performance Comparison")
        
        df = pd.DataFrame(channel_data)
        metrics = ['Subscribers', 'Views', 'Total_videos']
        
        fig = px.line(
            df, 
            x='Channel_name',
            y=metrics,
            title="Channel Metrics Comparison",
            labels={'value': 'Count', 'variable': 'Metric', 'Channel_name': 'Channel'},
            markers=True
        )
        fig.update_layout(
            yaxis_title="Count (Log Scale)",
            xaxis_title="Channel",
            legend_title="Metrics",
            hovermode="x unified",
            yaxis_type="log"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("Detailed Metrics:")
        display_df = df[['Channel_name'] + metrics].reset_index(drop=True)
        display_df.index = display_df.index + 1
        st.dataframe(
            display_df.style.format({
                'Subscribers': '{:,}',
                'Views': '{:,}',
                'Total_videos': '{:,}'
            })
        )
        
    except Exception as e:
        st.error(f"Failed to display channel comparison: {str(e)}")

def display_popular_videos(video_details):
    df = pd.DataFrame(video_details)
    channels = df['Channel'].unique()
    
    if len(channels) == 1:
        st.subheader(f"Popular Videos from {channels[0]}")
    else:
        st.subheader("Popular Videos from All Channels")
    
    for channel in channels:
        if len(channels) > 1:
            st.markdown(f"### {channel}")
        
        channel_videos = df[df['Channel'] == channel]
        top_videos = channel_videos.sort_values('Views', ascending=False).head(5)
        
        if not top_videos.empty:
            display_df = top_videos[['Title', 'Views', 'Likes', 'Comments', 'Published At']].reset_index(drop=True)
            display_df.index = display_df.index + 1
            st.dataframe(
                display_df,
                height=min(200, 35 * len(top_videos) + 35),
                use_container_width=True
            )
            
            fig = px.bar(
                top_videos,
                x='Title',
                y='Views',
                title=f"Top Videos" + ("" if len(channels) == 1 else f" from {channel}"),
                labels={'Views': 'View Count'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            if len(channels) > 1:
                st.write("---")
        else:
            st.warning(f"No videos found for {channel}")

def display_trend_analysis(video_details):
    try:
        st.subheader("Channel Performance Trends")
        
        if not video_details:
            st.warning("No video details available")
            return
            
        df = pd.DataFrame(video_details)
        df['Published At'] = pd.to_datetime(df['Published At'])
        df['Month'] = df['Published At'].dt.tz_localize(None).dt.to_period('M').dt.to_timestamp()
        all_channels = df['Channel'].unique()
        if len(all_channels) == 0:
            st.warning("No channels found in the data")
            return
            
        tabs = st.tabs([channel for channel in all_channels])
        
        for tab, channel in zip(tabs, all_channels):
            with tab:
                channel_df = df[df['Channel'] == channel]
                monthly_stats = channel_df.groupby('Month').agg({
                    'Views': 'sum',
                    'Likes': 'sum',
                    'Comments': 'sum'
                }).reset_index()
                
                fig = px.line(
                    monthly_stats,
                    x='Month',
                    y=['Views', 'Likes', 'Comments'],
                    title=f"Engagement Trends",
                    labels={'value': 'Count', 'variable': 'Metric'},
                    height=400
                )
                fig.update_traces(mode='lines+markers')
                st.plotly_chart(fig, use_container_width=True)
                
                display_df = monthly_stats.assign(
                    Month=monthly_stats['Month'].dt.strftime('%Y-%m')
                ).reset_index(drop=True)
                display_df.index = display_df.index + 1
                st.dataframe(
                    display_df.style.format({
                        'Views': '{:,}',
                        'Likes': '{:,}',
                        'Comments': '{:,}'
                    }),
                    use_container_width=True,
                    height=300
                )
                
    except Exception as e:
        st.error(f"Error displaying trends: {str(e)}")

def display_shorts_analysis(video_details):
    try:
        st.subheader("Shorts Performance Analysis by Channel")
        if not video_details:
            st.warning("No video details available")
            return
            
        df = pd.DataFrame(video_details)
        df['Duration (sec)'] = pd.to_timedelta(df['Duration']).dt.total_seconds()
        df['Video Type'] = df['Duration (sec)'].apply(lambda x: 'Shorts' if x <= 60 else 'Videos')
        channels = df['Channel'].unique()
        
        if len(channels) == 1:
            channel = channels[0]
            channel_df = df[df['Channel'] == channel]
            type_stats = channel_df.groupby('Video Type').agg({
                'Views': 'sum',
                'Title': 'count'
            }).rename(columns={'Title': 'Count'}).reset_index()
            
            total_videos = len(channel_df)
            total_views = channel_df['Views'].sum()
            shorts_count = type_stats[type_stats['Video Type'] == 'Shorts']['Count'].values[0] if not type_stats[type_stats['Video Type'] == 'Shorts'].empty else 0
            shorts_views = type_stats[type_stats['Video Type'] == 'Shorts']['Views'].values[0] if not type_stats[type_stats['Video Type'] == 'Shorts'].empty else 0
            
            st.markdown(f"### {channel}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Videos", total_videos)
                st.metric("Shorts Count", shorts_count, f"{shorts_count/total_videos*100:.1f}% of total")
            with col2:
                st.metric("Total Views", f"{total_views:,}")
                st.metric("Shorts Views", f"{shorts_views:,}", f"{shorts_views/total_views*100:.1f}% of total" if total_views > 0 else "0%")
            
            tab1, tab2, tab3 = st.tabs(["Count Comparison", "Views Comparison", "Top Shorts"])
            
            with tab1:
                fig_count = px.bar(
                    type_stats,
                    x='Video Type',
                    y='Count',
                    title="Shorts vs Regular Videos Count",
                    labels={'Video Type': 'Video Type', 'Count': 'Number of Videos'},
                    color='Video Type'
                )
                st.plotly_chart(fig_count, use_container_width=True)
                
                fig_pie_count = px.pie(
                    type_stats,
                    names='Video Type',
                    values='Count',
                    title="Percentage of Shorts vs Regular Videos",
                    labels={'Video Type': 'Video Type'}
                )
                st.plotly_chart(fig_pie_count, use_container_width=True)
            
            with tab2:
                fig_views = px.bar(
                    type_stats,
                    x='Video Type',
                    y='Views',
                    title="Views from Shorts vs Regular Videos",
                    labels={'Video Type': 'Video Type', 'Views': 'Total Views'},
                    color='Video Type'
                )
                st.plotly_chart(fig_views, use_container_width=True)
                
                fig_pie_views = px.pie(
                    type_stats,
                    names='Video Type',
                    values='Views',
                    title="Percentage of Views from Shorts vs Regular Videos",
                    labels={'Video Type': 'Video Type'}
                )
                st.plotly_chart(fig_pie_views, use_container_width=True)
            
            with tab3:
                shorts_df = channel_df[channel_df['Video Type'] == 'Shorts']
                if not shorts_df.empty:
                    display_df = shorts_df.sort_values('Views', ascending=False).head(10)[['Title', 'Views', 'Likes', 'Comments', 'Published At']].reset_index(drop=True)
                    display_df.index = display_df.index + 1
                    st.dataframe(
                        display_df,
                        use_container_width=True
                    )
                else:
                    st.warning(f"No shorts found for {channel}")
        
        else:
            tabs = st.tabs([f"{channel}" for channel in channels])
            
            for tab, channel in zip(tabs, channels):
                with tab:
                    channel_df = df[df['Channel'] == channel]
                    type_stats = channel_df.groupby('Video Type').agg({
                        'Views': 'sum',
                        'Title': 'count'
                    }).rename(columns={'Title': 'Count'}).reset_index()
                    
                    total_videos = len(channel_df)
                    total_views = channel_df['Views'].sum()
                    shorts_count = type_stats[type_stats['Video Type'] == 'Shorts']['Count'].values[0] if not type_stats[type_stats['Video Type'] == 'Shorts'].empty else 0
                    shorts_views = type_stats[type_stats['Video Type'] == 'Shorts']['Views'].values[0] if not type_stats[type_stats['Video Type'] == 'Shorts'].empty else 0
                    
                    st.markdown(f"### {channel} Shorts Analysis")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Videos", total_videos)
                        st.metric("Shorts Count", shorts_count, f"{shorts_count/total_videos*100:.1f}% of total")
                    with col2:
                        st.metric("Total Views", f"{total_views:,}")
                        st.metric("Shorts Views", f"{shorts_views:,}", f"{shorts_views/total_views*100:.1f}% of total" if total_views > 0 else "0%")
                    
                    subtab1, subtab2, subtab3 = st.tabs(["Count Comparison", "Views Comparison", "Top Shorts"])
                    
                    with subtab1:
                        fig_count = px.bar(
                            type_stats,
                            x='Video Type',
                            y='Count',
                            title="Shorts vs Regular Videos Count",
                            labels={'Video Type': 'Video Type', 'Count': 'Number of Videos'},
                            color='Video Type'
                        )
                        st.plotly_chart(fig_count, use_container_width=True)
                        
                        fig_pie_count = px.pie(
                            type_stats,
                            names='Video Type',
                            values='Count',
                            title="Percentage of Shorts vs Regular Videos",
                            labels={'Video Type': 'Video Type'}
                        )
                        st.plotly_chart(fig_pie_count, use_container_width=True)
                    
                    with subtab2:
                        fig_views = px.bar(
                            type_stats,
                            x='Video Type',
                            y='Views',
                            title="Views from Shorts vs Regular Videos",
                            labels={'Video Type': 'Video Type', 'Views': 'Total Views'},
                            color='Video Type'
                        )
                        st.plotly_chart(fig_views, use_container_width=True)
                        
                        fig_pie_views = px.pie(
                            type_stats,
                            names='Video Type',
                            values='Views',
                            title="Percentage of Views from Shorts vs Regular Videos",
                            labels={'Video Type': 'Video Type'}
                        )
                        st.plotly_chart(fig_pie_views, use_container_width=True)
                    
                    with subtab3:
                        shorts_df = channel_df[channel_df['Video Type'] == 'Shorts']
                        if not shorts_df.empty:
                            display_df = shorts_df.sort_values('Views', ascending=False).head(10)[['Title', 'Views', 'Likes', 'Comments', 'Published At']].reset_index(drop=True)
                            display_df.index = display_df.index + 1
                            st.dataframe(
                                display_df,
                                use_container_width=True
                            )
                        else:
                            st.warning(f"No shorts found for {channel}")
            
            st.markdown("### Channel Comparison: Shorts vs Videos Performance")
            summary_stats = []
            for channel in channels:
                channel_df = df[df['Channel'] == channel]
                total_videos = len(channel_df)
                shorts_count = len(channel_df[channel_df['Video Type'] == 'Shorts'])
                videos_count = len(channel_df[channel_df['Video Type'] == 'Videos'])
                total_views = channel_df['Views'].sum()
                shorts_views = channel_df[channel_df['Video Type'] == 'Shorts']['Views'].sum()
                videos_views = channel_df[channel_df['Video Type'] == 'Videos']['Views'].sum()
                
                summary_stats.append({
                    'Channel': channel,
                    'Total Videos': total_videos,
                    'Shorts Count': shorts_count,
                    'Shorts Percentage': (shorts_count / total_videos * 100) if total_videos > 0 else 0,
                    'Videos Count': videos_count,
                    'Videos Percentage': (videos_count / total_videos * 100) if total_videos > 0 else 0,
                    'Total Views': total_views,
                    'Shorts Views': shorts_views,
                    'Shorts Views Percentage': (shorts_views / total_views * 100) if total_views > 0 else 0,
                    'Videos Views': videos_views,
                    'Videos Views Percentage': (videos_views / total_views * 100) if total_views > 0 else 0
                })
            
            summary_df = pd.DataFrame(summary_stats).reset_index(drop=True)
            summary_df.index = summary_df.index + 1
            st.write("#### Performance Metrics by Channel")
            st.dataframe(
                summary_df.style.format({
                    'Shorts Percentage': '{:.1f}%',
                    'Videos Percentage': '{:.1f}%',
                    'Shorts Views Percentage': '{:.1f}%',
                    'Videos Views Percentage': '{:.1f}%',
                    'Total Videos': '{:,}',
                    'Shorts Count': '{:,}',
                    'Videos Count': '{:,}',
                    'Total Views': '{:,}',
                    'Shorts Views': '{:,}',
                    'Videos Views': '{:,}'
                }),
                use_container_width=True
            )
            
            comparison_data = []
            for channel in channels:
                channel_df = df[df['Channel'] == channel]
                shorts_count = len(channel_df[channel_df['Video Type'] == 'Shorts'])
                videos_count = len(channel_df[channel_df['Video Type'] == 'Videos'])
                shorts_views = channel_df[channel_df['Video Type'] == 'Shorts']['Views'].sum()
                videos_views = channel_df[channel_df['Video Type'] == 'Videos']['Views'].sum()
                
                comparison_data.extend([
                    {'Channel': channel, 'Type': 'Shorts', 'Count': shorts_count, 'Views': shorts_views},
                    {'Channel': channel, 'Type': 'Videos', 'Count': videos_count, 'Views': videos_views}
                ])
            
            comparison_df = pd.DataFrame(comparison_data)

            st.write("#### Video Count and Views Comparison")
            col1, col2 = st.columns(2)
            
            with col1:
                fig_count = px.bar(
                    comparison_df,
                    x='Channel',
                    y='Count',
                    color='Type',
                    title="Video Count by Type",
                    labels={'Count': 'Number of Videos', 'Channel': 'Channel'},
                    barmode='group',
                    color_discrete_map={'Shorts': '#FFA500', 'Videos': '#1F77B4'}
                )
                fig_count.update_layout(
                    showlegend=True,
                    legend_title='Video Type',
                    yaxis_title="Number of Videos"
                )
                st.plotly_chart(fig_count, use_container_width=True)
            
            with col2:
                fig_views = px.bar(
                    comparison_df,
                    x='Channel',
                    y='Views',
                    color='Type',
                    title="Video Views by Type",
                    labels={'Views': 'Total Views', 'Channel': 'Channel'},
                    barmode='group',
                    color_discrete_map={'Shorts': '#FFA500', 'Videos': '#1F77B4'}
                )
                fig_views.update_layout(
                    showlegend=True,
                    legend_title='Video Type',
                    yaxis_title="Total Views"
                )
                st.plotly_chart(fig_views, use_container_width=True)
                    
    except Exception as e:
        st.error(f"Failed to display shorts analysis: {e}")

def display_video_duration_analysis(video_details):
    try:
        st.subheader("Video Duration Analysis")
        if not video_details:
            st.warning("No video details available")
            return
            
        df = pd.DataFrame(video_details)
        df['Duration (minutes)'] = pd.to_timedelta(df['Duration']).dt.total_seconds() / 60

        df['Duration Category'] = pd.cut(
            df['Duration (minutes)'],
            bins=[0, 5, 20, float('inf')],
            labels=['Short (<5 mins)', 'Medium (5-20 mins)', 'Long (>20 mins)']
        )

        fig = px.histogram(df, x='Duration Category', color='Channel',
                          title="Video Duration Distribution by Channel",
                          barmode='group')
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Failed to display video duration analysis: {e}")

def display_publishing_frequency_analysis(video_details):
    try:
        st.subheader("Publishing Frequency Analysis")
        if not video_details:
            st.warning("No video details available")
            return
            
        df = pd.DataFrame(video_details)
        df['Published At'] = pd.to_datetime(df['Published At'])
        
        df_counts = df.groupby([pd.Grouper(key='Published At', freq='D'), 'Channel']).size().reset_index(name='Count')
        
        fig = px.line(df_counts, x='Published At', y='Count', color='Channel',
                     title="Publishing Frequency Over Time by Channel")
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Failed to display publishing frequency analysis: {e}")

def generate_pdf_report(channel_data, video_details):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)  # Use built-in Helvetica
  
  # Function to remove emojis and non-ASCII characters
    def remove_emojis(text):
        if isinstance(text, str):
            # Remove all non-ASCII characters
            return text.encode('ascii', 'ignore').decode('ascii')
        return str(text)

    # Add channel comparison data
    pdf.cell(200, 10, text="Channel Comparison", align="C")
    pdf.ln(10)
    for channel in channel_data:
        pdf.cell(200, 10, text=remove_emojis(f"Channel: {channel['Channel_name']}"))
        pdf.ln()  # Move to next line
        pdf.cell(200, 10, text=remove_emojis(f"Subscribers: {channel['Subscribers']}"))
        pdf.ln() 
        pdf.cell(200, 10, text=remove_emojis(f"Views: {channel['Views']}"))
        pdf.ln() 
        pdf.cell(200, 10, text=remove_emojis(f"Total Videos: {channel['Total_videos']}"))
        pdf.ln(10)

    # Add video details
    pdf.cell(200, 10, text="Video Details", align="C")
    pdf.ln(10)
    for video in video_details:
        pdf.cell(200, 10, text=remove_emojis(f"Channel: {video.get('Channel', 'N/A')}"))
        pdf.ln()  
        pdf.cell(200, 10, text=remove_emojis(f"Title: {video['Title']}"))
        pdf.ln()  
        pdf.cell(200, 10, text=remove_emojis(f"Views: {video['Views']}"))
        pdf.ln() 
        pdf.cell(200, 10, text=remove_emojis(f"Likes: {video['Likes']}"))
        pdf.ln()  
        pdf.cell(200, 10, text=remove_emojis(f"Comments: {video['Comments']}"))
        pdf.ln()
        pdf.ln()


    # Save the PDF to a file
    pdf_file = "analysis_report.pdf"
    pdf.output(pdf_file)
    return pdf_file

def main():
    
    st.title("YouTube Channel Analyzer")

    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("🔑 Enter your YouTube API Key", type="password")
        channel_names = st.text_area("📺 Enter channel names (one per line)").splitlines()
        channel_names = [name.strip() for name in channel_names if name.strip()]
        retries = st.slider("🔄 Retry attempts for API calls", min_value=1, max_value=10, value=3)
        initial_delay = st.slider("⏱️ Initial delay for retries (seconds)", min_value=1, max_value=10, value=5)

    if st.sidebar.button("Analyze"):
        if not api_key:
            st.error("Please enter a valid YouTube API Key.")
            return
        if not channel_names:
            st.error("Please enter at least one channel name.")
            return

        try:
            channel_data = []
            video_details_all = []

            progress_bar = st.progress(0)
            total_channels = len(channel_names)
            
            with st.spinner("Fetching channel data..."):
                for i, channel_name in enumerate(channel_names):
                    st.info(f"Fetching data for channel: {channel_name}")
                    channel_id = get_channel_id(channel_name, api_key)
                    if channel_id:
                        channel_stats = get_channel_stats(channel_id, api_key)
                        if channel_stats:
                            channel_data.append(channel_stats)
                            playlist_id = channel_stats['playlist_id']
                            video_ids = get_video_ids(playlist_id, api_key)
                            if video_ids:
                                video_details = fetch_video_details(video_ids, api_key)
                                for video in video_details:
                                    video['Channel'] = channel_stats['Channel_name']
                                video_details_all.extend(video_details)
                    progress_bar.progress((i + 1) / total_channels)

            if channel_data:
                st.success("Data fetching complete!")
                
                with st.expander("Channel Comparison", expanded=True):
                    display_channel_comparison(channel_data)
                
                if video_details_all:
                    with st.expander("Popular Videos"):
                        display_popular_videos(video_details_all)
                    with st.expander("Trend Analysis"):
                        display_trend_analysis(video_details_all)
                    with st.expander("Shorts Performance"):
                        display_shorts_analysis(video_details_all)
                    with st.expander("Video Duration Analysis"):
                        display_video_duration_analysis(video_details_all)
                    with st.expander("Publishing Frequency Analysis"):
                        display_publishing_frequency_analysis(video_details_all)

                    st.markdown("---")
                    st.subheader("📊 Report Generation")
                    
                    if st.write("Click below button to Generate and Download PDF........"):
                       st.write("")
                    else:
                       pdf_file = generate_pdf_report(channel_data, video_details_all)
                       with open(pdf_file, "rb") as file:
                         st.download_button(
                         label="⬇️ Download Analysis Report",
                         data=file,
                         file_name="analysis_report.pdf",
                         mime="application/pdf"
                         )
                else:
                    st.warning("No video details were fetched for the channels.")
                   
            else:
                st.error("No channel data was fetched. Please check your channel names and API key.")
        except Exception as e:
            st.error(f"An error occurred during analysis: {e}")

if __name__ == "__main__":
    main()