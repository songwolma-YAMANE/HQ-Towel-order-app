import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

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
st.markdown('<div class="sub-header">실시간 구글 스프레드시트 연동 및 스마트 대시보드</div>', unsafe_allow_html=True)

# 구글 스프레드시트 자동 연동
SHEET_ID = "13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=30)
def load_data():
    df_temp = pd.read_csv(url, header=None)
    header_row = 0
    for i in range(len(df_temp)):
        row_str = str(df_temp.iloc[i].values)
        if '출하처' in row_str or 'SHIPMENT' in row_str or '제품명' in row_str:
            header_row = i
            break
    df = pd.read_csv(url, header=header_row)
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    df = load_data()
    
    def find_col(keywords):
        for col in df.columns:
            for kw in keywords:
                if kw.lower() in col.lower():
                    return col
        return None

    date_col = find_col(['확정납기 1차', 'DELIVERY 1', '납기'])
    agency_col = find_col(['대리점', 'AGENCY'])
    ship_col = find_col(['출하처', 'SHIPMENT'])
    product_col = find_col(['제품명', 'KOREAN NAME'])
    completed_col = find_col(['출고 완료', '출고완료'])

    # --- 사이드바 보안 및 메뉴 설정 ---
    st.sidebar.header("🔐 보안 및 시스템 메뉴")
    
    # 관리자 비밀번호 (원하시는 문자로 언제든지 코드를 수정해 바꿀 수 있습니다)
    ADMIN_PASSWORD = "songwol1234" 
    
    input_pw = st.sidebar.text_input("관리자 비밀번호 입력", type="password", placeholder="관리자 전용 기능 해제")
    is_admin = (input_pw == ADMIN_PASSWORD)
    
    if is_admin:
        st.sidebar.success("🔓 관리자 모드가 활성화되었습니다.")
        menu = st.sidebar.radio("메뉴 선택", ["📊 종합 대시보드 & 알림", "📱 텔레그램 알림 전송", "📈 월별 수주 통계"])
    else:
        if input_pw:
            st.sidebar.error("❌ 비밀번호가 틀렸습니다. (일반 조회 모드)")
        else:
            st.sidebar.info("💡 일반 조회 모드 (검색 및 현황 확인 가능)")
        menu = st.sidebar.radio("메뉴 선택", ["📊 종합 대시보드 & 알림", "📈 월별 수주 통계"])

    # 날짜 데이터 정제
    today = pd.to_datetime(datetime.today().date())
    target_date = today + timedelta(days=7)
    
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    if menu == "📊 종합 대시보드 & 알림":
        # 요약 지표 카드
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="📋 전체 수주 건수", value=f"{len(df):,} 건")
        
        imminent_count = 0
        if date_col and date_col in df.columns:
            imminent_count = len(df[(df[date_col] >= today) & (df[date_col] <= target_date)])
            
        with col2:
            st.metric(label="🚨 7일 이내 납기 임박", value=f"{imminent_count} 건")
            
        completed_count = 0
        if completed_col and completed_col in df.columns:
            completed_count = len(df[df[completed_col].astype(str).str.upper() == 'O'])
            
        with col3:
            st.metric(label="✅ 출고 완료 건수", value=f"{completed_count} 건")
            
        st.markdown("---")
        
        # D-7 납기 임박 알림 섹션
        st.subheader("🚨 납기 임박 알림 (D-7 이내)")
        if date_col and date_col in df.columns:
            imminent_df = df[(df[date_col] >= today) & (df[date_col] <= target_date)]
            if not imminent_df.empty:
                st.warning(f"⚠️ 총 {len(imminent_df)}건의 제품이 7일 이내 납기를 앞두고 있습니다!")
                disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col] if c and c in df.columns]
                st.dataframe(imminent_df[disp_cols], use_container_width=True)
            else:
                st.success("🎉 향후 7일 이내 납기가 임박한 제품이 없습니다.")
        else:
            st.info("납기일 컬럼을 찾을 수 없습니다.")
                
        st.markdown("---")
        st.subheader("🔍 실시간 전체 오더 조회 및 필터링")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            search_query = st.text_input("🔍 출하처 또는 제품명 검색", "")
        with col_f2:
            if agency_col and agency_col in df.columns:
                agencies = ['전체'] + list(df[agency_col].dropna().unique())
                selected_agency = st.selectbox("🏢 대리점 선택 필터", agencies)
            else:
                selected_agency = '전체'
        
        filtered_df = df.copy()
        if search_query:
            cond = pd.Series(False, index=filtered_df.index)
            if ship_col and ship_col in filtered_df.columns:
                cond = cond | filtered_df[ship_col].astype(str).str.contains(search_query, na=False, case=False)
            if product_col and product_col in filtered_df.columns:
                cond = cond | filtered_df[product_col].astype(str).str.contains(search_query, na=False, case=False)
            filtered_df = filtered_df[cond]
            
        if selected_agency != '전체' and agency_col and agency_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[agency_col] == selected_agency]
            
        st.dataframe(filtered_df, use_container_width=True)

    elif menu == "📱 텔레그램 알림 전송" and is_admin:
        st.subheader("📱 텔레그램 납기 임박 알림 전송 설정")
        st.info("💡 텔레그램 봇 토큰과 채팅 ID를 입력하고 버튼을 누르면, 현재 납기가 임박한 오더 목록이 스마트폰 텔레그램 메신저로 즉시 전송됩니다.")
        
        with st.form("telegram_form"):
            bot_token = st.text_input("🤖 텔레그램 Bot Token", type="password", placeholder="예: 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
            chat_id = st.text_input("👤 텔레그램 Chat ID", placeholder="예: 987654321")
            submit_btn = st.form_submit_button("🚀 납기 임박 리스트 텔레그램으로 전송하기")
            
            if submit_btn:
                if not bot_token or not chat_id:
                    st.error("Bot Token과 Chat ID를 모두 입력해주세요.")
                else:
                    try:
                        if date_col and date_col in df.columns:
                            imminent_df = df[(df[date_col] >= today) & (df[date_col] <= today + timedelta(days=7))]
                        else:
                            imminent_df = pd.DataFrame()
                            
                        if imminent_df.empty:
                            msg = "🎉 [본사 수주 알림] 향후 7일 이내 납기가 임박한 제품이 없습니다."
                        else:
                            msg = f"🚨 [본사 수주 알림] 7일 이내 납기 임박 제품 ({len(imminent_df)}건):\n\n"
                            for idx, row in imminent_df.iterrows():
                                s = row.get(ship_col, '출하처 없음')
                                p = row.get(product_col, '제품명 없음')
                                d = str(row.get(date_col, ''))[:10]
                                msg += f"• 출하처: {s}\n  제품: {p}\n  납기: {d}\n\n"
                        
                        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        payload = {"chat_id": chat_id, "text": msg}
                        res = requests.post(tg_url, json=payload)
                        
                        if res.status_code == 200:
                            st.success("✅ 텔레그램 알림이 성공적으로 전송되었습니다!")
                        else:
                            st.error(f"❌ 전송 실패 (오류 코드: {res.status_code}) - 토큰과 Chat ID를 확인해주세요.")
                    except Exception as ex:
                        st.error(f"전송 중 오류 발생: {ex}")

    elif menu == "📈 월별 수주 통계":
        st.subheader("📈 월별 발주서 수령 현황 분석")
        date_rcv_col = find_col(['발주서 수령', '발주서'])
        if date_rcv_col and date_rcv_col in df.columns:
            df['수령_월'] = pd.to_datetime(df[date_rcv_col], errors='coerce').dt.to_period('M').astype(str)
            monthly_counts = df['수령_월'].value_counts().sort_index()
            st.bar_chart(monthly_counts)
        else:
            st.info("발주서 수령일 기준 통계를 생성할 수 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
