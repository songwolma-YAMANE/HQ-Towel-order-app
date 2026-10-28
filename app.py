from datetime import datetime, timedelta
import io
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(page_title="HQ Textile Order Management", layout="wide")

# CSS 스타일 적용
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📦 HQ Textile Order Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-time Google Sheets Integration & SCM Dashboard</div>', unsafe_allow_html=True)

# 구글 스프레드시트 데이터 로드
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
    
    pcs_col = find_col(['order pcs', 'pcs', '수량'])
    kg_col = find_col(['order kg', 'kg', '중량'])
    yarn_col = find_col(['yarn', '번수', '실'])
    width_col = find_col(['cm', '폭', '규격'])

    df['__PCS_NUM'] = pd.to_numeric(df[pcs_col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0).astype(float) if pcs_col in df.columns else 1
    df['__KG_NUM'] = pd.to_numeric(df[kg_col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0).astype(float) if kg_col in df.columns else 0

    def format_df_dates(input_df):
        d_df = input_df.copy()
        if date_col and date_col in d_df.columns:
            d_df[date_col] = pd.to_datetime(d_df[date_col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
            d_df[date_col] = d_df[date_col].replace('NaT', '')
        return d_df

    if 'order_memos' not in st.session_state:
        st.session_state.order_memos = {}

    # 사이드바 메뉴
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navigation", ["Dashboard & Orders", "Shipment Calendar", "Agency History", "Comparative Analysis", "Staff Memos"])
    today = pd.to_datetime(datetime.today().date())

    if date_col and date_col in df.columns:
        df['__PARSED_DATE'] = pd.to_datetime(df[date_col], errors='coerce')
        df['__YEAR'] = df['__PARSED_DATE'].dt.year.fillna(0).astype(int)
        df['__MONTH'] = df['__PARSED_DATE'].dt.to_period('M').astype(str)

    # 1. 대시보드
    if menu == "Dashboard & Orders":
        st.subheader("📊 Order Status Dashboard")
        total_len = len(df)
        completed_count = len(df[df[completed_col].astype(str).str.upper() == 'O']) if completed_col in df.columns else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Orders", f"{total_len:,}")
        with col2:
            st.metric("Completed", f"{completed_count:,}")
        with col3:
            rate = int((completed_count / total_len * 100) if total_len > 0 else 0)
            st.metric("Completion Rate", f"{rate}%")

        st.markdown("---")
        st.subheader("📋 Order List & Editor")
        
        search_query = st.text_input("Search Shipment or Product", "")
        filtered_df = df.copy()
        if search_query:
            cond = pd.Series(False, index=filtered_df.index)
            if ship_col in filtered_df.columns:
                cond = cond | filtered_df[ship_col].astype(str).str.contains(search_query, na=False, case=False)
            if product_col in filtered_df.columns:
                cond = cond | filtered_df[product_col].astype(str).str.contains(search_query, na=False, case=False)
            filtered_df = filtered_df[cond]

        editor_df = filtered_df.drop(columns=['__PARSED_DATE', '__YEAR', '__MONTH', '__PCS_NUM', '__KG_NUM'], errors='ignore')
        st.data_editor(format_df_dates(editor_df), use_container_width=True)

    # 2. 캘린더 뷰
    elif menu == "Shipment Calendar":
        st.subheader("📅 Monthly Shipment Calendar")
        if date_col in df.columns:
            valid_df = df.dropna(subset=[date_col]).copy()
            valid_df['YearMonth'] = valid_df[date_col].dt.to_period('M').astype(str)
            ym_list = sorted(valid_df['YearMonth'].unique(), reverse=True)
            if ym_list:
                selected_ym = st.selectbox("Select Year-Month", ym_list)
                month_df = valid_df[valid_df['YearMonth'] == selected_ym]
                st.dataframe(format_df_dates(month_df), use_container_width=True)
            else:
                st.warning("No date data found.")
        else:
            st.warning("Date column not found.")

    # 3. 대리점 이력
    elif menu == "Agency History":
        st.subheader("🏢 Agency & Shipment History")
        if agency_col in df.columns:
            selected_target = st.selectbox("Select Agency", df[agency_col].dropna().unique())
            target_df = df[df[agency_col] == selected_target]
            st.dataframe(format_df_dates(target_df), use_container_width=True)
        else:
            st.warning("Agency column not found.")

    # 4. 비교 분석
    elif menu == "Comparative Analysis":
        st.subheader("📈 Comparative Analysis")
        if '__YEAR' in df.columns:
            yearly_summary = df[df['__YEAR'] > 0].groupby('__YEAR').agg({'__YEAR': 'count', '__KG_NUM': 'sum'}).rename(columns={'__YEAR': 'Orders', '__KG_NUM': 'Total_Kg'}).reset_index()
            st.dataframe(yearly_summary, use_container_width=True)
            st.bar_chart(yearly_summary.set_index('__YEAR')['Orders'])
        else:
            st.warning("Year data not available.")

    # 5. 메모 관리
    elif menu == "Staff Memos":
        st.subheader("📝 Staff Memos")
        if ship_col and product_col in df.columns:
            df['오더표시'] = df.index.astype(str) + " | " + df[ship_col].astype(str) + " | " + df[product_col].astype(str)
            selected_label = st.selectbox("Select Order", df['오더표시'].tolist())
            idx = int(selected_label.split(" | ")[0])
            
            memo = st.text_area("Enter Memo", value=st.session_state.order_memos.get(idx, ""))
            if st.button("Save Memo"):
                st.session_state.order_memos[idx] = memo
                st.success("Saved!")
        else:
            st.warning("Required columns not found.")

except Exception as e:
    st.error(f"Error loading data: {e}")
