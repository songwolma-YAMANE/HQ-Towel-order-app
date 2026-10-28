from datetime import datetime, timedelta
import io
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(page_title="본사 문직 수주/출고 관리 시스템", layout="wide")

# HTML/CSS 커스텀 디자인 적용
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# 다국어 텍스트 사전 (Localization Dictionary)
LANG_DICT = {
    "한국어": {
        "title": "📦 본사 문직 제품 수주 및 출고 관리 시스템",
        "subtitle": (
            "실시간 구글 스프레드시트 연동 및 스마트 SCM 엔터프라이즈 대시보드"
        ),
        "sec_menu": "🔐 보안 및 시스템 메뉴",
        "pw_label": "관리자 비밀번호 입력",
        "pw_placeholder": "관리자 전용 기능 해제",
        "admin_success": "🔓 관리자 모드가 활성화되었습니다.",
        "pw_error": "❌ 비밀번호가 틀렸습니다. (일반 조회 모드)",
        "general_info": "💡 일반 조회 모드 (검색 및 현황 확인 가능)",
        "menu_1": "📊 종합 대시보드 & 지연/임박 알림",
        "menu_2": "📅 출고 캘린더 뷰",
        "menu_3": "🏢 대리점/출하처별 상세 이력",
        "menu_4": "📈 연도/월별 및 상세 비교 분석",
        "menu_5": "📝 실무자 메모 및 특이사항",
        "menu_6": "📜 변경 이력 로그 (Audit Trail)",
        "total_orders": "📋 전체 수주 건수",
        "overdue_orders": "🔥 납기 지연 (Overdue)",
        "d7_imminent": "🚨 7일 이내 납기",
        "d30_expect": "📅 1달 후(30일) 예정",
        "completion_rate": "🎯 전체 출고 달성률",
        "search_box": "🔍 출하처 또는 제품명 검색",
        "agency_filter": "🏢 대리점 선택 필터",
        "excel_btn": "📥 엑셀로 다운로드",
    },
    "English": {
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": (
            "Real-time Google Sheets Integration & Smart SCM Enterprise"
            " Dashboard"
        ),
        "sec_menu": "🔐 Security & System Menu",
        "pw_label": "Enter Admin Password",
        "pw_placeholder": "Unlock admin features",
        "admin_success": "🔓 Admin mode activated.",
        "pw_error": "❌ Incorrect password. (General view mode)",
        "general_info": (
            "💡 General view mode (Search & status check available)"
        ),
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
        "excel_btn": "📥 Download Excel",
    },
}

# --- 사이드바 언어 선택 ---
st.sidebar.markdown("---")
selected_lang = st.sidebar.selectbox("🌐 Language / 언어", ["한국어", "English"])
t = LANG_DICT[selected_lang]

# 타이틀 디자인 적용
st.markdown(
    f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True
)
st.markdown(
    f'<div class="sub-header">{t["subtitle"]}</div>', unsafe_allow_html=True
)

# 구글 스프레드시트 자동 연동
SHEET_ID = "13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


@st.cache_data(ttl=30)
def load_data():
    df_temp = pd.read_csv(url, header=None)
    header_row = 0
    for i in range(len(df_temp)):
        row_str = str(df_temp.iloc[i].values)
        if "출하처" in row_str or "SHIPMENT" in row_str or "제품명" in row_str:
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

    date_col = find_col(["확정납기 1차", "DELIVERY 1", "납기"])
    date_rcv_col = find_col(["발주서 수령", "발주서"])
    agency_col = find_col(["대리점", "AGENCY"])
    ship_col = find_col(["출하처", "SHIPMENT"])
    product_col = find_col(["제품명", "KOREAN NAME"])
    completed_col = find_col(["출고 완료", "출고완료"])

    pcs_col = find_col(["order pcs", "pcs", "수량"])
    kg_col = find_col(["order kg", "kg", "중량"])
    yarn_col = find_col(["yarn", "번수", "실"])
    width_col = find_col(["cm", "폭", "규격"])

    if pcs_col and pcs_col in df.columns:
        df["__PCS_NUM"] = (
            pd.to_numeric(
                df[pcs_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                errors="coerce",
            )
            .fillna(0)
            .astype(float)
        )
    else:
        df["__PCS_NUM"] = 1

    if kg_col and kg_col in df.columns:
        df["__KG_NUM"] = (
            pd.to_numeric(
                df[kg_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                errors="coerce",
            )
            .fillna(0)
            .astype(float)
        )
    else:
        df["__KG_NUM"] = 0

    def format_df_dates(input_df):
        d_df = input_df.copy()
        if date_col and date_col in d_df.columns:
            d_df[date_col] = (
                pd.to_datetime(d_df[date_col], errors="coerce")
                .dt.strftime("%Y-%m-%d")
                .fillna("")
            )
            d_df[date_col] = d_df[date_col].replace("NaT", "")
        return d_df

    if "order_memos" not in st.session_state:
        st.session_state.order_memos = {}

    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = []

    # --- 사이드바 보안 설정 (Streamlit Secrets 활용) ---
    st.sidebar.header(t["sec_menu"])
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "songwol1234")

    input_pw = st.sidebar.text_input(
        t["pw_label"], type="password", placeholder=t["pw_placeholder"]
    )
    is_admin = input_pw == ADMIN_PASSWORD

    if is_admin:
        st.sidebar.success(t["admin_success"])
        menu_options = [
            t["menu_1"],
            t["menu_2"],
            t["menu_3"],
            t["menu_4"],
            t["menu_5"],
            t["menu_6"],
        ]
    else:
        if input_pw:
            st.sidebar.error(t["pw_error"])
        else:
            st.sidebar.info(t["general_info"])
        menu_options = [
            t["menu_1"],
            t["menu_2"],
            t["menu_3"],
            t["menu_4"],
            t["menu_5"],
            t["menu_6"],
        ]

    menu = st.sidebar.radio("Menu", menu_options)

    today = pd.to_datetime(datetime.today().date())

    base_date_for_stat = (
        date_rcv_col if (date_rcv_col and date_rcv_col in df.columns) else date_col
    )
    if base_date_for_stat and base_date_for_stat in df.columns:
        df["__PARSED_DATE"] = pd.to_datetime(df[base_date_for_stat], errors="coerce")
        df["__YEAR"] = df["__PARSED_DATE"].dt.year.fillna(0).astype(int)
        df["__MONTH"] = df["__PARSED_DATE"].dt.to_period("M").astype(str)

    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # 1. 메뉴 1: 종합 대시보드 & 지연/임박 알림
    if menu == t["menu_1"]:
        target_d7 = today + timedelta(days=7)
        target_d30 = today + timedelta(days=30)

        valid_years = df[df["__YEAR"] > 0]["__YEAR"]
        latest_year = (
            int(valid_years.max())
            if not valid_years.empty
            else datetime.today().year
        )

        df_latest = df[df["__YEAR"] == latest_year]
        total_latest = len(df_latest)

        if completed_col and completed_col in df_latest.columns:
            pending_latest = len(
                df_latest[
                    df_latest[completed_col].astype(str).str.upper() != "O"
                ]
            )
        else:
            pending_latest = total_latest

        total_len = len(df)
        completed_count = 0
        if completed_col and completed_col in df.columns:
            completed_count = len(
                df[df[completed_col].astype(str).str.upper() == "O"]
            )

        overdue_df = pd.DataFrame()
        if date_col in df.columns:
            if completed_col in df.columns:
                overdue_df = df[
                    (df[date_col] < today)
                    & (df[completed_col].astype(str).str.upper() != "O")
                ]
            else:
                overdue_df = df[df[date_col] < today]
        overdue_count = len(overdue_df)

        imminent_d7_df = pd.DataFrame()
        if date_col in df.columns:
            imminent_d7_df = df[
                (df[date_col] >= today) & (df[date_col] <= target_d7)
            ]
        imminent_d7 = len(imminent_d7_df)

        completion_rate = int(
            (completed_count / total_len * 100) if total_len > 0 else 0
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label=f"🌟 {latest_year}년 신규 수주 건수",
                value=f"{total_latest:,}건",
            )
        with col2:
            st.metric(
                label=f"⏳ {latest_year}년 출하 대기 건수",
                value=f"{pending_latest:,}건",
                delta=(
                    f"진행중 {pending_latest}" if pending_latest > 0 else "완료"
                ),
                delta_color="off",
            )
        with col3:
            st.metric(
                label=t["overdue_orders"],
                value=f"{overdue_count}",
                delta=(
                    f"-{overdue_count}" if overdue_count > 0 else "0"
                ),
                delta_color="inverse",
            )
        with col4:
            st.metric(
                label=t["d7_imminent"],
                value=f"{imminent_d7}",
                delta=(
                    f"{imminent_d7}건 집중" if imminent_d7 > 0 else "0"
                ),
                delta_color="off",
            )

        with st.expander(
            f"📁 과거 연도별 오더 수주 건수 보기 (2023년 ~ {latest_year - 1}년)",
            expanded=False,
        ):
            past_df = df[(df["__YEAR"] > 0) & (df["__YEAR"] < latest_year)]
            if not past_df.empty:
                past_summary = (
                    past_df.groupby("__YEAR")
                    .agg(
                        오더건수=("__YEAR", "count"),
                        총중량_Kg=("__KG_NUM", "sum"),
                        총수량_PCS=("__PCS_NUM", "sum"),
                    )
                    .reset_index()
                    .sort_values(by="__YEAR", ascending=False)
                )
                st.dataframe(past_summary, use_container_width=True)
            else:
                st.info("조회된 과거 연도 데이터가 없습니다.")

        st.markdown(
            f"**전체 누적 달성률 ({latest_year}년 포함 총 {total_len}건 중"
            f" {completed_count}건 완료): {completion_rate}%**"
        )
        st.progress(completion_rate / 100.0)

        st.markdown("---")

        if overdue_count > 0:
            st.error(
                f"🔥 **[긴급 경고] 납기일이 지났으나 아직 출고되지 않은 오더가"
                f" 총 {overdue_count}건 있습니다! 확인이 필요합니다.**"
            )
            with st.expander(
                f"🔥 납기 지연 오더 상세 보기 ({overdue_count}건)",
                expanded=True,
            ):
                disp_cols = [
                    c
                    for c in [
                        ship_col,
                        agency_col,
                        product_col,
                        "ORDER PCS",
                        date_col,
                        completed_col,
                    ]
