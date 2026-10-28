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
    .main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .stAlert { border-radius: 0.5rem; }
    </style>
""",
    unsafe_allow_html=True,
)

# 다국어 텍스트 사전
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
        "search_box": "Search Shipment or Product",
        "agency_filter": "Agency Filter",
        "excel_btn": "Download Excel",
    },
}

# 사이드바 언어 선택
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

# 구글 스프레드시트 CSV 내보내기 링크
url = "https://docs.google.com/spreadsheets/d/13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg/export?format=csv"


@st.cache_data(ttl=30)
def load_data():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    df_temp = pd.read_csv(io.BytesIO(res.content), header=None)
    header_row = 0
    for i in range(
