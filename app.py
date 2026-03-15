import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px

def get_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def get_enhanced_channel_data(youtube, channel_name):
    search_res = youtube.search().list(q=channel_name, type='channel', part='snippet', maxResults=1).execute()
    if not search_res['items']: return None
    c_id = search_res['items'][0]['id']['channelId']
    c_title = search_res['items'][0]['snippet']['title']
    c_stat = youtube.channels().list(id=c_id, part='statistics,snippet').execute()['items'][0]
    
    # 월간 분석의 정확도를 높이기 위해 최근 10개 영상 가져오기
    v_res = youtube.search().list(channelId=c_id, part='snippet', order='date', maxResults=10, type='video').execute()
    video_ids = [item['id']['videoId'] for item in v_res['items']]
    v_stats = youtube.videos().list(id=",".join(video_ids), part='statistics,snippet').execute()
    
    video_data = []
    for v in v_stats['items']:
        video_data.append({
            'title': v['snippet']['title'][:20] + "...",
            'views': int(v['statistics']['viewCount']),
            'date': v['snippet']['publishedAt'][:10]
        })
    return {
        'title': c_title, 'stats': c_stat['statistics'],
        'thumbnail': c_stat['snippet']['thumbnails']['default']['url'],
        'recent_videos': pd.DataFrame(video_data)
    }

st.set_page_config(page_title="YouTube Channel Analyzer Pro", layout="wide")
st.title("📊 소셜블레이드형 채널 분석기 (Pro 버전)")

st.markdown("### 🔑 분석 준비 (아래 빈칸을 채워주세요)")
col_api, col_query = st.columns(2)
with col_api:
    api_key = st.text_input("1. YouTube API Key 입력", type="password")
with col_query:
    query = st.text_input("2. 분석할 채널명 입력", placeholder="예: 슈카월드")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🚀 종합 분석 시작하기", use_container_width=True) and api_key and query:
    youtube = get_youtube_client(api_key)
    try:
        data = get_enhanced_channel_data(youtube, query)
        if data:
            st.divider()
            # 1. 채널 기본 정보
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                st.image(data['thumbnail'], width=150)
            with col2:
                st.subheader(data['title'])
                st.metric("총 구독자 수", f"{int(data['stats']['subscriberCount']):,}명")
            with col3:
                st.metric("누적 총 조회수", f"{int(data['stats']['viewCount']):,}회")
                st.metric("총 업로드 영상 수", f"{int(data['stats']['videoCount']):,}개")

            st.divider()
            
            # 2. 월간 예상 총수익 계산 알고리즘
            df = data['recent_videos']
            df['date'] = pd.to_datetime(df['date'])
            
            if len(df) > 1:
                days_diff = (df['date'].max() - df['date'].min()).days
                upload_freq = days_diff / len(df) if days_diff > 0 else 1.0
            else:
                upload_freq = 7.0
            
            videos_per_month = 30 / upload_freq if upload_freq > 0 else 1
            avg_views = df['views'].mean()
            
            est_monthly_views = (videos_per_month * avg_views) * 1.5
            
            min_monthly_rev = (est_monthly_views / 1000) * 1.0
            max_monthly_rev = (est_monthly_views / 1000) * 3.0
            exchange_rate = 1350
            
            st.subheader("💰 채널 월간 예상 총수익 (소셜블레이드 추정 방식)")
            st.info(f"💡 **분석 결과:** 최근 영상 업로드 주기(평균 **{upload_freq:.1f}일**에 1개)와 과거 영상의 지속적인 조회수를 종합하여, 한 달(30일) 누적 조회수를 약 **{est_monthly_views:,.0f}회**로 추정했습니다.")
            
            rev_col1, rev_col2 = st.columns(2)
            rev_col1.success(f"📉 최저 예상 월 수익 (CPM $1.0)\n\n### ${min_monthly_rev:,.0f}\n**(약 {int(min_monthly_rev * exchange_rate):,}원)**")
            rev_col2.warning(f"📈 최고 예상 월 수익 (CPM $3.0)\n\n### ${max_monthly_rev:,.0f}\n**(약 {int(max_monthly_rev * exchange_rate):,}원)**")

            st.divider()

            # 3. 최근 10개 영상 성과 차트
            st.subheader("📈 최근 10개 영상 성과 추이 (떡상/하락 지표)")
            fig = px.line(df, x='date', y='views', text='views', markers=True)
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error("오류가 발생했습니다. API Key가 정확한지 확인해 주세요.")
