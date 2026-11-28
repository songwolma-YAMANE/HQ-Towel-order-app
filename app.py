from datetime import datetime, timedelta
import base64
import io
import re
import time
import unicodedata
from PIL import Image
import pandas as pd
import requests
import streamlit as st

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(
    page_title="HQ Textile Order & Shipment Management", layout="wide"
)

# [보안 수정 1] 공유된 링크(URL)에 로그인/비밀번호 파라미터가 묻어 들어오는 것 원천 차단
try:
    if len(st.query_params) > 0:
        st.query_params.clear()
except Exception:
    pass


def get_secret(key, default):
    """secrets.toml이 없어도 오류 없이 기본값을 반환"""
    try:
        return str(st.secrets.get(key, default))
    except Exception:
        return str(default)


# HTML/CSS 커스텀 디자인 적용
st.markdown(
    """
<style>
.main-header { font-size: 2.2rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem; }
.sub-header { font-size: 1.1rem; color: #4B5563; margin-bottom: 1.5rem; }
.stAlert { border-radius: 0.5rem; }

.brand-logo-container {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 15px;
}
</style>
""",
    unsafe_allow_html=True,
)

# 다국어 텍스트 사전
LANG_DICT = {
    "한국어": {
        "title": "📦 본사 문직 제품 수주 및 출고 관리 시스템",
        "subtitle": "실시간 구글 스프레드시트 연동 대시보드",
        "login_title": "🔐 시스템 로그인",
        "login_desc": "관리자 또는 일반 뷰어 비밀번호를 입력해 주세요.",
        "login_btn": "로그인",
        "logo_header": "🖼️ 로고 이미지 업로드 및 크기 통일",
        "logo_1": "첫 번째 로고 (SONGWOL)",
        "logo_2": "두 번째 로고 (SONGWOL VINA)",
        "logo_info": (
            "👈 사이드바에서 두 개의 로고 이미지 파일을 각각"
            " 업로드해주시면, 높이가 자동으로 똑같이 맞춰져서 상단에"
            " 표시됩니다."
        ),
        "sec_menu": "🔐 보안 및 시스템 로그인",
        "refresh_btn": "🔄 데이터 새로고침 (즉시 반영)",
        "pw_label": "비밀번호 입력",
        "pw_placeholder": "관리자 또는 일반 뷰어 비밀번호",
        "admin_success": "🔓 최고 관리자 모드 활성화",
        "viewer_success": "👁️ 일반 뷰어 모드로 접속 중",
        "pw_error": "❌ 비밀번호 오류",
        "logout_btn": "로그아웃",
        "menu_title": "메뉴",
        "menu_1": "📊 대시보드",
        "menu_2": "📅 출하 캘린더",
        "menu_3": "🏢 대리점 이력",
        "menu_4": "📈 비교 분석",
        "menu_5": "📝 메모 관리",
        "menu_6": "📈 방문자 통계 (관리자 전용)",
        "metric_total_orders": "{year} 전체 오더",
        "metric_completed": "{year} 출고 완료",
        "metric_total_pcs": "{year} 전체 PCS",
        "metric_weight": "{year} 전체 중량",
        "search_box": "🔍 검색 및 자동완성 (출하처/제품명/ERP명)",
        "search_help": (
            "키를 입력하거나 목록에서 선택하면 연관 단어가 자동완성됩니다."
        ),
        "direct_search": "통합 검색 (출하처 / 한글 제품명 / 영어 ERP명 / 대리점 / 색상 등 전체)",
        "direct_search_ph": "예: 인스파이어, scrub, ivory, waffle, FT170 등 직접 입력 후 Enter",
        "search_result": "검색 결과: 총 {count:,}건",
        "unit_count": "건",
        "save_btn": "메모 저장",
        "save_success": "저장되었습니다!",
        "no_data": "데이터가 없습니다.",
        "admin_only_warn": "관리자 권한이 필요합니다.",
    },
    "English": {
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": "Real-time Google Sheets Dashboard",
        "login_title": "🔐 System Login",
        "login_desc": "Please enter the Admin or Viewer password.",
        "login_btn": "Sign In",
        "logo_header": "🖼️ Upload & Resize Logos",
        "logo_1": "First Logo (SONGWOL)",
        "logo_2": "Second Logo (SONGWOL VINA)",
        "logo_info": (
            "👈 Please upload two logo image files from the sidebar. Their"
            " heights will be automatically adjusted to match."
        ),
        "sec_menu": "🔐 Security & Login",
        "refresh_btn": "🔄 Refresh Data (Immediate)",
        "pw_label": "Enter Password",
        "pw_placeholder": "Admin or Viewer password",
        "admin_success": "🔓 Admin mode active.",
        "viewer_success": "👁️ Viewer mode active.",
        "pw_error": "❌ Incorrect password",
        "logout_btn": "Logout",
        "menu_title": "Menu",
        "menu_1": "📊 Dashboard",
        "menu_2": "📅 Shipment Calendar",
        "menu_3": "🏢 History",
        "menu_4": "📈 Analysis",
        "menu_5": "📝 Memos",
        "menu_6": "📈 Visitor Stats (Admin Only)",
        "metric_total_orders": "{year} Total Orders",
        "metric_completed": "{year} Completed",
        "metric_total_pcs": "{year} Total PCS",
        "metric_weight": "{year} Total Weight",
        "search_box": "🔍 Search & Auto-complete (Shipment/Product/ERP)",
        "search_help": (
            "Type keys or select from the list to auto-complete related words."
        ),
        "direct_search": "Unified Search (Shipment / Product / ERP Name / Agency / Color)",
        "direct_search_ph": "e.g., Inspire, scrub, ivory, waffle, FT170...",
        "search_result": "Matching Orders: {count:,}",
        "unit_count": "Orders",
        "save_btn": "Save Memo",
        "save_success": "Saved successfully!",
        "no_data": "No data available.",
        "admin_only_warn": "Admin access required.",
    },
}

# 사이드바 언어 선택
st.sidebar.markdown("---")
selected_lang = st.sidebar.selectbox("🌐 Language", ["한국어", "English"])
t = LANG_DICT[selected_lang]

# [보안 수정 2] 사용자별 독립 세션(st.session_state) 기반 관리자/일반 뷰어 로그인 분리
# - URL 파라미터나 서버 공용 캐시에 로그인 정보를 저장하지 않으므로 링크를 공유해도 자동 로그인되지 않음
if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = None

ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "songwol1234")
VIEWER_PASSWORD = get_secret("VIEWER_PASSWORD", "viewer1234")

if st.session_state["auth_role"] is None:
    st.markdown(f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{t["subtitle"]}</div>', unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.subheader(t["login_title"])
        st.caption(t["login_desc"])
        with st.form("login_form", clear_on_submit=True):
            input_pw = st.text_input(
                t["pw_label"],
                type="password",
                placeholder=t["pw_placeholder"],
            )
            submitted = st.form_submit_button(
                t["login_btn"], use_container_width=True
            )

        if submitted:
            if input_pw == ADMIN_PASSWORD:
                st.session_state["auth_role"] = "admin"
                st.rerun()
            elif input_pw == VIEWER_PASSWORD:
                st.session_state["auth_role"] = "viewer"
                st.rerun()
            else:
                st.error(t["pw_error"])

    # 로그인 전에는 시트 데이터와 대시보드 화면을 렌더링하지 않음
    st.stop()

is_admin = st.session_state["auth_role"] == "admin"

# 사이드바 로고 업로드
st.sidebar.markdown("---")
st.sidebar.subheader(t["logo_header"])
uploaded_logo1 = st.sidebar.file_uploader(
    t["logo_1"], type=["png", "jpg", "jpeg"]
)
uploaded_logo2 = st.sidebar.file_uploader(
    t["logo_2"], type=["png", "jpg", "jpeg"]
)


def resize_uploaded_image(uploaded_file, target_height=40):
    try:
        img = Image.open(uploaded_file)
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        target_width = int(target_height * aspect_ratio)

        img_resized = img.resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        )
        buffered = io.BytesIO()
        img_resized.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception:
        return ""


logo1_base64 = (
    resize_uploaded_image(uploaded_logo1, target_height=40)
    if uploaded_logo1
    else ""
)
logo2_base64 = (
    resize_uploaded_image(uploaded_logo2, target_height=40)
    if uploaded_logo2
    else ""
)

if logo1_base64 and logo2_base64:
    st.markdown(
        f"""
    <div class="brand-logo-container">
        <img src="data:image/png;base64,{logo1_base64}" alt="SONGWOL">
        <img src="data:image/png;base64,{logo2_base64}" alt="SONGWOL VINA">
    </div>
    """,
        unsafe_allow_html=True,
    )
else:
    st.info(t["logo_info"])

st.markdown(f'<div class="main-header">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{t["subtitle"]}</div>', unsafe_allow_html=True)

BASE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg/export?format=csv"
)


def safe_parse_dates(series):
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(r
