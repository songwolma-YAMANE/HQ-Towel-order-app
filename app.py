import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(page_title="본사 문직 수주/출고 관리 시스템", layout="wide")

# HTML/CSS 커스텀 디자인 적용
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stAlert {
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# 타이틀 디자인
st.markdown('<div class="main-header">📦 본사 문직 제품 수주 및 출고 관리 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">실시간 구글 스프레드시트 연동 및 종합 관리 대시보드</div>', unsafe_allow_html=True)

# 구글 스프레드시트 자동 연동
SHEET_ID = "13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=30)
def load_data():
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
    
    # 사이드바 메뉴 및 필터 구성
    st.sidebar.header("🛠️ 시스템 메뉴")
    menu = st.sidebar.radio("이동할 메뉴 선택", ["📊 종합 대시보드 & 알림", "✏️ 오더 데이터 직접 편집", "📈 월별 수주 통계"])
    
    # 날짜 데이터 정제
    date_col = '확정납기 1차 (DELIVERY 1)'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    if menu == "📊 종합 대시보드 & 알림":
        # 요약 지표 카드 (Metrics)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="📋 전체 수주 건수", value=f"{len(df):,} 건")
        
        today = pd.to_datetime(datetime.today().date())
        target_date = today + timedelta(days=7)
        if date_col in df.columns:
            imminent_count = len(df[(df[date_col] >= today) & (df[date_col] <= target_date)])
        else:
            imminent_count = 0
        with col2:
            st.metric(label="🚨 7일 이내 납기 임박", value=f"{imminent_count} 건")
            
        completed_col = '출고 완료'
        if completed_col in df.columns:
            completed_count = len(df[df[completed_col].astype(str).str.upper() == 'O'])
        else:
            completed_count = 0
        with col3:
            st.metric(label="✅ 출고 완료 건수", value=f"{completed_count} 건")
            
        st.markdown("---")
        
        # D-7 납기 임박 알림 섹션
        st.subheader("🚨 납기 임박 알림 (D-7 이내)")
        if date_col in df.columns:
            imminent_df = df[(df[date_col] >= today) & (df[date_col] <= target_date)]
            if not imminent_df.empty:
                st.warning(f"⚠️ 총 {len(imminent_df)}건의 제품이 7일 이내 납기를 앞두고 있습니다!")
                display_cols = [c for c in ['출하처 (SHIPMENT)', '대리점 (AGENCY)', '제품명 (KOREAN NAME)', 'ORDER PCS', date_col] if c in df.columns]
                st.dataframe(imminent_df[display_cols], use_container_width=True)
            else:
                st.success("🎉 향후 7일 이내 납기가 임박한 제품이 없습니다.")
                
        st.markdown("---")
        st.subheader("🔍 실시간 전체 오더 조회 및 필터링")
        
        # 검색 및 대리점별 필터 강화
        col_f1, col_f2 = st.columns(2)
        agency_col = '대리점 (AGENCY)'
        ship_col = '출하처 (SHIPMENT)'
        
        with col_f1:
            search_query = st.text_input("🔍 출하처 또는 제품명 검색", "")
        with col_f2:
            if agency_col in df.columns:
                agencies = ['전체'] + list(df[agency_col].dropna().unique())
                selected_agency = st.selectbox("🏢 대리점 선택 필터", agencies)
            else:
                selected_agency = '전체'
        
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df[ship_col].astype(str).str.contains(search_query, na=False) |
                filtered_df['제품명 (KOREAN NAME)'].astype(str).str.contains(search_query, na=False)
            ]
        if selected_agency != '전체':
            filtered_df = filtered_df[filtered_df[agency_col] == selected_agency]
            
        st.dataframe(filtered_df, use_container_width=True)

    elif menu == "✏️ 오더 데이터 직접 편집":
        st.subheader("✏️ 웹 화면 직접 편집기 (Data Editor)")
        st.info("💡 표 안의 셀을 더블클릭하여 내용을 자유롭게 수정하거나 새로운 행을 추가할 수 있습니다. 수정한 후 아래 다운로드 버튼을 눌러 구글 시트에 반영하세요.")
        
        # 데이터 에디터 제공
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        # 변경된 데이터 다운로드 기능
        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 수정된 데이터 파일 다운로드 (구글 시트 업로드용)",
            data=csv_data,
            file_name="HQ_본사_문직_수주_출고_수정본.csv",
            mime="text/csv",
        )

    elif menu == "📈 월별 수주 통계":
        st.subheader("📈 월별 발주서 수령 현황 분석")
        date_rcv_col = '발주서 수령'
        if date_rcv_col in df.columns:
            df['수령_월'] = pd.to_datetime(df[date_rcv_col], errors='coerce').dt.to_period('M').astype(str)
            monthly_counts = df['수령_월'].value_counts().sort_index()
            st.bar_chart(monthly_counts)
        else:
            st.info("발주서 수령일 기준 통계를 생성할 수 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
