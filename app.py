import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="본사 문직 수주/출고 관리", layout="wide")
st.title("📦 본사 문직 제품 수주 및 출고 관리 대시보드")

# 구글 스프레드시트 연동 또는 엑셀 파일 로드
@st.cache_data(ttl=600)
def load_data():
    df = pd.read_excel("HQ_본사_문직_수주_출고_리스트 FN.xlsx")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

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

search_query = st.text_input("🔍 출하처 또는 제품명 검색", "")
if search_query:
    filtered_df = df[
        df['출하처 (SHIPMENT)'].astype(str).str.contains(search_query, na=False) |
        df['제품명 (KOREAN NAME)'].astype(str).str.contains(search_query, na=False)
    ]
else:
    filtered_df = df

st.dataframe(filtered_df, use_container_width=True)