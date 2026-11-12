from datetime import datetime, timedelta
import base64
import io
import time
from PIL import Image
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
        "pw_label": "관리자 비밀번호 입력",
        "pw_placeholder": "비밀번호",
        "admin_success": "🔓 관리자 모드 활성화",
        "pw_error": "❌ 비밀번호 오류",
        "general_info": "💡 일반 조회 모드",
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
        "
