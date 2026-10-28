from datetime import datetime, timedelta
import io
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(page_title="HQ Textile Order & Shipment Management", layout="wide")

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
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": "Real-time Google Sheets Integration & Smart SCM Enterprise Dashboard",
        "sec_menu": "🔐 Security & System Menu",
        "pw_label": "Enter Admin Password",
        "pw_placeholder": "Unlock admin features",
        "admin_success": "🔓 Admin mode activated.",
        "pw_error": "❌ Incorrect password. (General view mode)",
        "general_info": "💡 General view mode (Search & status check available)",
        "menu_1": "📊 Dashboard & Alerts",
        "menu_2": "📅 Shipment Calendar",
        "menu_3": "🏢 Agency/Shipment History",
        "menu_4": "📈 Comparative Analysis",
        "menu_5": "📝 Staff Memos",
        "menu_6": "📜 Audit Trail",
        "total_orders": "Total Orders",
        "overdue_orders": "Overdue Orders",
        "d7_imminent": "Due within 7 Days",
        "search_box": "Search Shipment or Product",
        "agency_filter": "Agency Filter",
        "excel_btn": "Download Excel"
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
        "menu_1": "📊 Dashboard & Alerts",
        "menu_2": "📅 Shipment Calendar",
        "menu_3": "🏢 Agency/Shipment History",
        "menu_4": "📈 Comparative Analysis",
        "menu_5": "📝 Staff Memos",
        "menu_6": "📜 Audit Trail",
        "total_orders": "Total Orders",
        "overdue_orders": "Overdue Orders",
        "d7_imminent": "Due within 7 Days",
        "search_box": "Search Shipment or Product",
        "agency_filter": "Agency Filter",
        "excel_btn": "Download Excel"
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
    
    pcs_col = find_col(['order pcs', 'pcs', '수량'])
    kg_col = find_col(['order kg', 'kg', '중량'])
    yarn_col = find_col(['yarn', '번수', '실'])
    width_col = find_col(['cm', '폭', '규격'])

    if pcs_col and pcs_col in df.columns:
        df['__PCS_NUM'] = pd.to_numeric(df[pcs_col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0).astype(float)
    else:
        df['__PCS_NUM'] = 1
        
    if kg_col and kg_col in df.columns:
        df['__KG_NUM'] = pd.to_numeric(df[kg_col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0).astype(float)
    else:
        df['__KG_NUM'] = 0

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

    # --- 사이드바 보안 설정 ---
    st.sidebar.header(t["sec_menu"])
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "songwol1234")
    
    input_pw = st.sidebar.text_input(t["pw_label"], type="password", placeholder=t["pw_placeholder"])
    is_admin = (input_pw == ADMIN_PASSWORD)
    
    if is_admin:
        st.sidebar.success(t["admin_success"])
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

    # 1. 메뉴 1: 대시보드
    if menu == t["menu_1"]:
        target_d7 = today + timedelta(days=7)

        valid_years = df[df['__YEAR'] > 0]['__YEAR']
        latest_year = int(valid_years.max()) if not valid_years.empty else datetime.today().year

        df_latest = df[df['__YEAR'] == latest_year]
        total_latest = len(df_latest)
        
        if completed_col and completed_col in df_latest.columns:
            pending_latest = len(df_latest[df_latest[completed_col].astype(str).str.upper() != 'O'])
        else:
            pending_latest = total_latest

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
            st.metric(label=f"New Orders ({latest_year})", value=f"{total_latest:,}")
        with col2:
            st.metric(label=f"Pending ({latest_year})", value=f"{pending_latest:,}")
        with col3:
            st.metric(label="Overdue Orders", value=f"{overdue_count}")
        with col4:
            st.metric(label="Due in 7 Days", value=f"{imminent_d7}")

        with st.expander(f"Past Years Summary (~ {latest_year - 1})", expanded=False):
            past_df = df[(df['__YEAR'] > 0) & (df['__YEAR'] < latest_year)]
            if not past_df.empty:
                past_summary = past_df.groupby('__YEAR').agg({'__YEAR': 'count', '__KG_NUM': 'sum', '__PCS_NUM': 'sum'}).rename(columns={'__YEAR': 'Orders', '__KG_NUM': 'Total_Kg', '__PCS_NUM': 'Total_Pcs'}).reset_index().sort_values(by='__YEAR', ascending=False)
                st.dataframe(past_summary, use_container_width=True)
            else:
                st.info("No past year data found.")

        st.markdown(f"**Overall Completion Rate ({completed_count}/{total_len}): {completion_rate}%**")
        st.progress(completion_rate / 100.0)
            
        st.markdown("---")
        
        if overdue_count > 0:
            st.error(f"Warning: There are {overdue_count} overdue orders!")
            with st.expander(f"Overdue Details ({overdue_count})", expanded=True):
                disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                st.dataframe(format_df_dates(overdue_df)[disp_cols], use_container_width=True)

        if imminent_d7 > 0:
            st.warning(f"Notice: {imminent_d7} orders are due within 7 days.")
        
        with st.expander(f"Imminent Orders ({imminent_d7})", expanded=True):
            if not imminent_d7_df.empty:
                disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                st.dataframe(format_df_dates(imminent_d7_df)[disp_cols], use_container_width=True)
            else:
                st.success("No orders due in the next 7 days.")
                
        st.markdown("---")
        st.subheader("Search & Filter")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search_query = st.text_input("Search Keyword", "")
        with col_f2:
            if agency_col and agency_col in df.columns:
                agencies = ['All'] + list(df[agency_col].dropna().unique())
                selected_agency = st.selectbox("Agency Filter", agencies)
            else:
                selected_agency = 'All'
        with col_f3:
            use_date_filter = st.checkbox("Custom Date Range Filter")
        
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

        st.markdown("### Real-time Order Editor")
        st.info("Edit cells directly below. You can download changes via Excel.")
        
        editor_df = filtered_df.drop(columns=['__PARSED_DATE', '__YEAR', '__MONTH', '__PCS_NUM', '__KG_NUM'], errors='ignore')
        cols_to_drop = [c for c in editor_df.columns if '5차' in c or 'delivery 5' in c.lower()]
        editor_df = editor_df.drop(columns=cols_to_drop, errors='ignore')

        edited_df = st.data_editor(format_df_dates(editor_df), use_container_width=True, num_rows="dynamic")

        col_res1, col_res2 = st.columns([3, 1])
        with col_res1:
            st.write(f"Found **{len(edited_df):,}** orders.")
        with col_res2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                format_df_dates(editor_df).to_excel(writer, index=False, sheet_name='Orders')
            excel_data = output.getvalue()
            st.download_button(
                label=t["excel_btn"],
                data=excel_data,
                file_name=f"Order_List_{datetime.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # 2. 메뉴 2: 캘린더 뷰
    elif menu == t["menu_2"]:
        st.subheader("Monthly Shipment Calendar")
        if date_col in df.columns:
            valid_df = df.dropna(subset=[date_col]).copy()
            valid_df['YearMonth'] = valid_df[date_col].dt.to_period('M').astype(str)
            ym_list = sorted(valid_df['YearMonth'].unique(), reverse=True)
            
            if ym_list:
                selected_ym = st.selectbox("Select Year-Month", ym_list)
                month_df = valid_df[valid_df['YearMonth'] == selected_ym].sort_values(by=date_col, ascending=False)
                st.markdown(f"### {selected_ym} Orders (Total: {len(month_df)})")
                disp_cols = [c for c in [date_col, ship_col, agency_col, product_col, 'ORDER PCS', completed_col] if c and c in df.columns]
                st.dataframe(format_df_dates(month_df)[disp_cols], use_container_width=True)
            else:
                st
