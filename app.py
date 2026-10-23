import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="본사 문직 수주/출고 관리", layout="wide")
st.title("📦 본사 문직 제품 수주 및 출고 관리 대시보드")

# 구글 스프레드시트 자동 연동 (공유된 링크를 통해 실시간 로드)
SHEET_ID = "13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    # 시트 상단의 제목이나 빈 행을 자동으로 건너뛰고 '출하처'가 있는 행을 찾아 제목으로 지정
    df_temp = pd.read_csv(url, header=None)
    header_row = 0
    for i in range(len(df_temp)):
        row_str = str(df_temp.iloc[i].values)
        if '출하처' in row_str or 'SHIPMENT' in row_str:
            header_row = i
            break
    
    df = pd.read_csv(url, header=header_row)
    return df

try:
    df = load_data()
    
    # 납기 7일 전 알림 기능
    st.subheader("🚨 납기 임박 알림 (D-7 이내)")
    date_col = '확정납기 1차 (DELIVERY 1)'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        today = pd.to_datetime(datetime.today().date())
        target_date = today + timedelta(days=7)
        imminent_df = df[(df[date_col] >= today) & (df[date_col] <= target_date)]
        
        if not imminent_df.empty:
            st.warning(f"총 {len(imminent_df)}건의 제품이 7일 이내 납기를 앞두고 있습니다!")
            st.dataframe(imminent_df[['출하처 (SHIPMENT)', '제품명 (KOREAN NAME)', 'ORDER PCS', date_col]])
        else:
            st.info("향후 7일 이내 납기가 임박한 제품이 없습니다.")

    st.markdown("---")
    st.subheader("📋 전체 수주 및 출고 리스트")
    
    # 검색 기능
    search_query = st.text_input("🔍 출하처 또는 제품명 검색", "")
    if search_query:
        filtered_df = df[
            df['출하처 (SHIPMENT)'].astype(str).str.contains(search_query, na=False) |
            df['제품명 (KOREAN NAME)'].astype(str).str.contains(search_query, na=False)
        ]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
