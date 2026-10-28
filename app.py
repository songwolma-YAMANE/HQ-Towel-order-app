from datetime import datetime, timedelta
import io
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(
    page_title="HQ Textile Order & Shipment Management", layout="wide"
)

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
        "menu_1": "📊 종합 대시보드 & 알림",
        "menu_2": "📅 출고 캘린더",
        "menu_3": "🏢 대리점/출하처별 상세 이력",
        "menu_4": "📈 비교 분석",
        "menu_5": "📝 실무자 메모",
        "menu_6": "📜 변경 이력 로그",
        "total_orders": "전체 수주 건수",
        "overdue_orders": "납기 지연",
        "d7_imminent": "7일 이내 납기",
        "search_box": "출하처 또는 제품명 검색",
        "agency_filter": "대리점 선택",
        "excel_btn": "엑셀로 다운로드",
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
        "excel_btn": "Download Excel",
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

# 구글 스프레드시트 링크 설정 (웹에 게시된 CSV 링크 또는 기본 export 링크)
url = "https://docs.google.com/spreadsheets/d/13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg/export?format=csv"


@st.cache_data(ttl=30)
def load_data():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    df_temp = pd.read_csv(io.BytesIO(response.content), header=None)
    header_row = 0
    for i in range(len(df_temp)):
        row_str = str(df_temp.iloc[i].values)
        if "출하처" in row_str or "SHIPMENT" in row_str or "제품명" in row_str:
            header_row = i
            break
    df = pd.read_csv(io.BytesIO(response.content), header=header_row)
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
