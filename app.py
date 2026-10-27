import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import io

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

# 다국어 텍스트 사전 (Localization Dictionary)
LANG_DICT = {
    "한국어": {
        "title": "📦 본사 문직 제품 수주 및 출고 관리 시스템",
        "subtitle": "실시간 구글 스프레드시트 연동 및 스마트 SCM 엔터프라이즈 대시보드",
        "sec_menu": "🔐 보안 및 시스템 메뉴",
        "pw_label": "관리자 비밀번호 입력",
        "pw_placeholder": "관리자 전용 기능 해제",
        "admin_success": "🔓 관리자 모드가 활성화되었습니다.",
        "pw_error": "❌ 비밀번호가 틀렸습니다. (일반 조회 모드)",
        "general_info": "💡 일반 조회 모드 (검색 및 현황 확인 가능)",
        "menu_1": "📊 종합 대시보드 & 지연/임박 알림",
        "menu_2": "📅 출고 캘린더 뷰",
        "menu_3": "🏢 대리점/출하처별 상세 이력",
        "menu_4": "📈 연도/월별 및 상세 비교 분석 (New)",
        "menu_5": "📝 실무자 메모 및 특이사항",
        "menu_6": "📜 변경 이력 로그 (Audit Trail)",
        "total_orders": "📋 전체 수주 건수",
        "overdue_orders": "🔥 납기 지연 (Overdue)",
        "d7_imminent": "🚨 7일 이내 납기",
        "d30_expect": "📅 1달 후(30일) 예정",
        "completion_rate": "🎯 전체 출고 달성률",
        "search_box": "🔍 출하처 또는 제품명 검색",
        "agency_filter": "🏢 대리점 선택 필터",
        "excel_btn": "📥 엑셀로 다운로드"
    },
    "English": {
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": "Real-time Google Sheets Integration & Smart SCM Enterprise Dashboard",
        "sec_menu": "🔐 Security & System Menu",
        "pw_label": "Enter Admin Password",
        "pw_placeholder": "Unlock admin features",
        "admin_success": "🔓 Admin mode activated.",
        "pw_error": "❌ Incorrect password. (General view mode)",
        "general_info": "💡 General view mode (Search & status check available)",
        "menu_1": "📊 Dashboard & Overdue/Imminent Alerts",
        "menu_2": "📅 Shipment Calendar View",
        "menu_3": "🏢 Agency/Shipment History",
        "menu_4": "📈 Annual/Monthly & Detailed Comparative Analysis",
        "menu_5": "📝 Staff Memos & Notes",
        "menu_6": "📜 Audit Trail & Change Logs",
        "total_orders": "📋 Total Orders",
        "overdue_orders": "🔥 Overdue Orders",
        "d7_imminent": "🚨 Due within 7 Days",
        "d30_expect": "📅 Due within 30 Days",
        "completion_rate": "🎯 Overall Shipment Rate",
        "search_box": "🔍 Search Shipment or Product",
        "agency_filter": "🏢 Agency Filter",
        "excel_btn": "📥 Download Excel"
    }
}

# --- 사이드바 언어 선택 ---
st.sidebar.markdown("---")
selected_lang = st.sidebar.selectbox("🌐 Language / 언어", ["한국어", "English"])
t = LANG_DICT[selected_lang]

# 타이틀 디자인 적용
st.markdown(f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{t["subtitle"]}</div>', unsafe_allow_html=True)

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
    date_rcv_col = find_col(['발주서 수령', '발주서'])
    agency_col = find_col(['대리점', 'AGENCY'])
    ship_col = find_col(['출하처', 'SHIPMENT'])
    product_col = find_col(['제품명', 'KOREAN NAME'])
    completed_col = find_col(['출고 완료', '출고완료'])
    
    # 추가 비교 분석을 위한 컬럼 자동 매핑
    pcs_col = find_col(['order pcs', 'pcs', '수량'])
    kg_col = find_col(['order kg', 'kg', '중량'])
    yarn_col = find_col(['yarn', '번수', '실'])
    width_col = find_col(['cm', '폭', '규격'])

    # 숫자형 데이터 변환 전처리 (계산을 위해 쉼표 및 단위 제거)
    if pcs_col and pcs_col in df.columns:
        df['__PCS_NUM'] = pd.to_numeric(df[pcs_col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    else:
        df['__PCS_NUM'] = 1 # 컬럼이 없을 경우 기본 건수 단위
        
    if kg_col and kg_col in df.columns:
        df['__KG_NUM'] = pd.to_numeric(df[kg_col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    else:
        df['__KG_NUM'] = 0

    # 화면 출력용 날짜 포맷 함수
    def format_df_dates(input_df):
        d_df = input_df.copy()
        if date_col and date_col in d_df.columns:
            d_df[date_col] = pd.to_datetime(d_df[date_col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
            d_df[date_col] = d_df[date_col].replace('NaT', '')
        return d_df

    if 'order_memos' not in st.session_state:
        st.session_state.order_memos = {}
        
    if 'audit_logs' not in st.session_state:
        st.session_state.audit_logs = []

    # --- 사이드바 보안 및 메뉴 설정 ---
    st.sidebar.header(t["sec_menu"])
    ADMIN_PASSWORD = "songwol1234" 
    
    input_pw = st.sidebar.text_input(t["pw_label"], type="password", placeholder=t["pw_placeholder"])
    is_admin = (input_pw == ADMIN_PASSWORD)
    
    if is_admin:
        st.sidebar.success(t["admin_success"])
        menu_options = [t["menu_1"], t["menu_2"], t["menu_3"], t["menu_4"], t["menu_5"], t["menu_6"]]
    else:
        if input_pw:
            st.sidebar.error(t["pw_error"])
        else:
            st.sidebar.info(t["general_info"])
        menu_options = [t["menu_1"], t["menu_2"], t["menu_3"], t["menu_4"], t["menu_5"], t["menu_6"]]

    menu = st.sidebar.radio("Menu", menu_options)

    today = pd.to_datetime(datetime.today().date())
    
    base_date_for_stat = date_rcv_col if (date_rcv_col and date_rcv_col in df.columns) else date_col
    if base_date_for_stat and base_date_for_stat in df.columns:
        df['__PARSED_DATE'] = pd.to_datetime(df[base_date_for_stat], errors='coerce')
        df['__YEAR'] = df['__PARSED_DATE'].dt.year.fillna(0).astype(int)
        df['__MONTH'] = df['__PARSED_DATE'].dt.to_period('M').astype(str)

    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # 1. 메뉴 1: 종합 대시보드 & 지연/임박 알림
    if menu == t["menu_1"]:
        target_d7 = today + timedelta(days=7)
        target_d30 = today + timedelta(days=30)

        total_len = len(df)
        completed_count = 0
        if completed_col and completed_col in df.columns:
            completed_count = len(df[df[completed_col].astype(str).str.upper() == 'O'])
        
        overdue_df = pd.DataFrame()
        if date_col in df.columns:
            if completed_col in df.columns:
                overdue_df = df[(df[date_col] < today) & (df[completed_col].astype(str).str.upper() != 'O')]
            else:
                overdue_df = df[df[date_col] < today]
        overdue_count = len(overdue_df)

        imminent_d7_df = pd.DataFrame()
        if date_col in df.columns:
            imminent_d7_df = df[(df[date_col] >= today) & (df[date_col] <= target_d7)]
        imminent_d7 = len(imminent_d7_df)

        completion_rate = int((completed_count / total_len * 100) if total_len > 0 else 0)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label=t["total_orders"], value=f"{total_len:,}")
        with col2:
            st.metric(label=t["overdue_orders"], value=f"{overdue_count}", delta=f"-{overdue_count}" if overdue_count > 0 else "0", delta_color="inverse")
        with col3:
            st.metric(label=t["d7_imminent"], value=f"{imminent_d7}", delta=f"{imminent_d7}건 집중 관리" if imminent_d7 > 0 else "0", delta_color="off")
        
        imminent_d30 = len(df[(df[date_col] > target_d7) & (df[date_col] <= target_d30)]) if date_col in df.columns else 0
        with col4:
            st.metric(label=t["d30_expect"], value=f"{imminent_d30}")

        st.markdown(f"**{t['completion_rate']}: {completion_rate}% ({completed_count} / {total_len})**")
        st.progress(completion_rate / 100.0)
            
        st.markdown("---")
        
        if overdue_count > 0:
            st.error(f"🔥 **[긴급 경고] 납기일이 지났으나 아직 출고되지 않은 오더가 총 {overdue_count}건 있습니다! 확인이 필요합니다.**")
            with st.expander(f"🔥 납기 지연 오더 상세 보기 ({overdue_count}건)", expanded=True):
                disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                st.dataframe(format_df_dates(overdue_df)[disp_cols], use_container_width=True)

        if imminent_d7 > 0:
            st.warning(f"🚨 **[필독] 향후 7일 이내에 출고/납기가 도래하는 긴급 오더가 총 {imminent_d7}건 있습니다.**")
        
        with st.expander(f"🚨 [집중 관리] 7일 이내 납기 임박 오더 ({imminent_d7}건)", expanded=True):
            if not imminent_d7_df.empty:
                disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                st.dataframe(format_df_dates(imminent_d7_df)[disp_cols], use_container_width=True)
            else:
                st.success("🎉 향후 7일 이내 납기가 임박한 제품이 없습니다.")

        with st.expander(f"📅 Within 30 Days ({imminent_d30})", expanded=False):
            if date_col and date_col in df.columns:
                df_d30 = df[(df[date_col] > target_d7) & (df[date_col] <= target_d30)]
                if not df_d30.empty:
                    disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                    st.dataframe(format_df_dates(df_d30)[disp_cols], use_container_width=True)
                else:
                    st.info("No orders expected in this period.")
                
        st.markdown("---")
        st.subheader(t["search_box"])
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search_query = st.text_input(t["search_box"], "")
        with col_f2:
            if agency_col and agency_col in df.columns:
                agencies = ['All'] + list(df[agency_col].dropna().unique())
                selected_agency = st.selectbox(t["agency_filter"], agencies)
            else:
                selected_agency = 'All'
        with col_f3:
            use_date_filter = st.checkbox("📅 Custom Date Range Filter")
        
        filtered_df = df.copy()
        
        if search_query:
            cond = pd.Series(False, index=filtered_df.index)
            if ship_col and ship_col in filtered_df.columns:
                cond = cond | filtered_df[ship_col].astype(str).str.contains(search_query, na=False, case=False)
            if product_col and product_col in filtered_df.columns:
                cond = cond | filtered_df[product_col].astype(str).str.contains(search_query, na=False, case=False)
            filtered_df = filtered_df[cond]
            
        if selected_agency != 'All' and agency_col and agency_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[agency_col] == selected_agency]

        if use_date_filter and date_col in filtered_df.columns:
            valid_dates = filtered_df[date_col].dropna()
            if not valid_dates.empty:
                min_d = valid_dates.min().date()
                max_d = valid_dates.max().date()
                date_range = st.date_input("Select date range", [min_d, max_d])
                if len(date_range) == 2:
                    start_r, end_r = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                    filtered_df = filtered_df[(filtered_df[date_col] >= start_r) & (filtered_df[date_col] <= end_r)]

        if date_col and date_col in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by=date_col, ascending=False)

        st.markdown("### 📋 실시간 오더 편집 및 확인 에디터")
        st.info("💡 표 내부의 셀을 직접 클릭하여 수정하거나 상태를 확인하고, 변경 사항은 엑셀로 다운로드할 수 있습니다.")
        
        editor_df = filtered_df.drop(columns=['__PARSED_DATE', '__YEAR', '__MONTH', '__PCS_NUM', '__KG_NUM'], errors='ignore')
        cols_to_drop = [c for c in editor_df.columns if '5차' in c or 'delivery 5' in c.lower()]
        editor_df = editor_df.drop(columns=cols_to_drop, errors='ignore')

        edited_df = st.data_editor(
