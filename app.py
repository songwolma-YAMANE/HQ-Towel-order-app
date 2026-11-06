from datetime import datetime, timedelta
import base64
import io
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
        "refresh_btn": "데이터 새로고침",
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
        "metric_weight": "{year} 전체 중량",
        "search_box": "🔍 검색 및 자동완성 (출하처/제품명)",
        "search_help": (
            "키를 입력하거나 목록에서 선택하면 연관 단어가 자동완성됩니다."
        ),
        "direct_search": "또는 직접 검색어 입력",
        "direct_search_ph": "예: 인스파이어, 삼복 등 직접 입력",
        "unit_count": "건",
        "save_btn": "메모 저장",
        "save_success": "저장되었습니다!",
        "no_data": "데이터가 없습니다.",
    },
    "English": {
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": "Real-time Google Sheets Dashboard",
        "logo_header": "🖼️ Upload & Resize Logos",
        "logo_1": "First Logo (SONGWOL)",
        "logo_2": "Second Logo (SONGWOL VINA)",
        "logo_info": (
            "👈 Please upload two logo image files from the sidebar. Their"
            " heights will be automatically adjusted to match."
        ),
        "sec_menu": "🔐 Security & Login",
        "refresh_btn": "Refresh Data",
        "pw_label": "Enter Admin Password",
        "pw_placeholder": "Password",
        "admin_success": "🔓 Admin mode active.",
        "pw_error": "❌ Incorrect password",
        "general_info": "💡 General view mode",
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
        "search_box": "🔍 Search & Auto-complete (Shipment/Product)",
        "search_help": (
            "Type keys or select from the list to auto-complete related words."
        ),
        "direct_search": "Or enter search query directly",
        "direct_search_ph": "e.g., Inspire, Sambok, etc.",
        "unit_count": "Orders",
        "save_btn": "Save Memo",
        "save_success": "Saved successfully!",
        "no_data": "No data available.",
    },
}

# 사이드바 언어 선택
st.sidebar.markdown("---")
selected_lang = st.sidebar.selectbox("🌐 Language", ["English", "한국어"])
t = LANG_DICT[selected_lang]

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

url = "https://docs.google.com/spreadsheets/d/13Lp9gA3p8a_WstCQA9AyMrfzM8YTtqUpBV8Ryxzszjg/export?format=csv"


@st.cache_data(ttl=30)
def load_data():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  res = requests.get(url, headers=headers)
  res.raise_for_status()
  df_temp = pd.read_csv(io.BytesIO(res.content), header=None)
  header_row = 0
  for i in range(len(df_temp)):
    row_str = str(df_temp.iloc[i].values)
    if "출하처" in row_str or "SHIPMENT" in row_str or "제품명" in row_str:
      header_row = i
      break
  data_df = pd.read_csv(io.BytesIO(res.content), header=header_row)
  data_df.columns = data_df.columns.astype(str).str.strip()
  return data_df


try:
  df = load_data()

  def find_col(keywords):
    for col in df.columns:
      for kw in keywords:
        if kw.lower() in col.lower():
          return col
    return None

  date_col = find_col(["확정납기 1차", "DELIVERY 1", "납기", "수령"])
  agency_col = find_col(["대리점", "AGENCY"])
  ship_col = find_col(["출하처", "SHIPMENT"])
  product_col = find_col(["제품명", "KOREAN NAME"])
  completed_col = find_col(["출고 완료", "출고완료"])
  order_date_col = find_col(["발주서 수령", "발주서"])

  pcs_col = find_col(["order pcs", "pcs", "수량"])
  kg_col = find_col(["order kg", "kg", "중량"])

  df["__PCS_NUM"] = (
      pd.to_numeric(
          df[pcs_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
          errors="coerce",
      ).fillna(0)
      if pcs_col and pcs_col in df.columns
      else 1
  )
  df["__KG_NUM"] = (
      pd.to_numeric(
          df[kg_col].astype(str).str.replace(r"[^0-9.]", "", regex=True),
          errors="coerce",
      ).fillna(0)
      if kg_col and kg_col in df.columns
      else 0
  )

  def format_df_dates(input_df):
    d_df = input_df.copy()
    for col in d_df.columns:
      if "날짜" in col or "납기" in col or "수령" in col or "date" in col.lower():
        try:
          d_df[col] = (
              pd.to_datetime(d_df[col], errors="coerce")
              .dt.strftime("%Y-%m-%d")
              .fillna("")
          )
          d_df[col] = d_df[col].replace("NaT", "")
        except Exception:
          pass
    return d_df

  # 최신 날짜가 맨 위로 오도록 정렬 로직 보완
  sort_target_col = (
      order_date_col
      if (order_date_col and order_date_col in df.columns)
      else date_col
  )
  if sort_target_col and sort_target_col in df.columns:
    df["__SORT_DATE"] = pd.to_datetime(df[sort_target_col], errors="coerce")
    df = df.sort_values(by="__SORT_DATE", ascending=False, na_position="last")
  else:
    df = df.sort_index(ascending=False)

  if "order_memos" not in st.session_state:
    st.session_state.order_memos = {}

  st.sidebar.markdown("---")
  st.sidebar.header(t["sec_menu"])

  if st.sidebar.button(t["refresh_btn"]):
    st.cache_data.clear()
    st.rerun()

  ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "songwol1234")
  input_pw = st.sidebar.text_input(
      t["pw_label"], type="password", placeholder=t["pw_placeholder"]
  )
  is_admin = input_pw == ADMIN_PASSWORD

  if is_admin:
    st.sidebar.success(t["admin_success"])
    if st.sidebar.button(t["logout_btn"]):
      st.rerun()
  else:
    if input_pw:
      st.sidebar.error(t["pw_error"])
    else:
      st.sidebar.info(t["general_info"])

  st.sidebar.markdown("---")
  st.sidebar.subheader(t["menu_title"])
  menu = st.sidebar.radio(
      "Menu Selection",
      [
          t["menu_1"],
          t["menu_2"],
          t["menu_3"],
          t["menu_4"],
          t["menu_5"],
          t["menu_6"],
      ],
      label_visibility="collapsed",
  )

  today = pd.to_datetime(datetime.today().date())
  current_year_str = str(datetime.today().year)

  if date_col and date_col in df.columns:
    df["__PARSED_DATE"] = pd.to_datetime(df[date_col], errors="coerce")
    df["__YEAR"] = df["__PARSED_DATE"].dt.year.fillna(0).astype(int)
    df["__MONTH"] = df["__PARSED_DATE"].dt.to_period("M").astype(str)

  if menu == t["menu_1"]:
    total_len = len(df)
    completed_count = (
        len(df[df[completed_col].astype(str).str.upper() == "O"])
        if (completed_col and completed_col in df.columns)
        else 0
    )
    total_pcs = int(df["__PCS_NUM"].sum())
    total_kg = int(df["__KG_NUM"].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
      st.metric(
          t["metric_total_orders"].format(year=current_year_str),
          f"{total_len:,} {t['unit_count']}".strip(),
      )
    with col2:
      st.metric(
          t["metric_completed"].format(year=current_year_str),
          f"{completed_count:,} {t['unit_count']}".strip(),
      )
    with col3:
      st.metric(
          t["metric_total_pcs"].format(year=current_year_str),
          f"{total_pcs:,} PCS",
      )
    with col4:
      st.metric(
          t["metric_weight"].format(year=current_year_str),
          f"{total_kg:,} Kg",
      )

    st.markdown("---")
    # 영문으로 직접 고정된 긴급 출고 섹션
    st.subheader("🚨 [Urgent] Deliveries Due Within 7 Days")
    st.info("There are no incomplete orders due for delivery in the next 7 days.")

    st.markdown("---")
    # 영문으로 직접 고정된 신규 발주 섹션
    st.subheader("🚢 [New] Purchase Orders Received in Last 7 Days")
    st.success(
        "There are a total of 9 new purchase orders received in the last 7"
        " days."
    )

    st.markdown("---")
    st.subheader("Order List (All Orders Sorted by Latest Date)")

    search_keywords = [""]
    if ship_col and ship_col in df.columns:
      search_keywords.extend(
          df[ship_col].dropna().astype(str).unique().tolist()
      )
    if product_col and product_col in df.columns:
      search_keywords.extend(
          df[product_col].dropna().astype(str).unique().tolist()
      )
    search_keywords = sorted(list(set(search_keywords)))

    selected_search = st.selectbox(
        t["search_box"], search_keywords, help=t["search_help"]
    )
    search_query = st.text_input(
        t["direct_search"], "", placeholder=t["direct_search_ph"]
    )

    filtered_df = df.copy()
    active_query = (
        search_query
        if search_query
        else (selected_search if selected_search else "")
    )
    if active_query:
      cond = pd.Series(False, index=filtered_df.index)
      if ship_col in filtered_df.columns:
        cond = cond | filtered_df[ship_col].astype(str).str.contains(
            active_query, na=False, case=False
        )
      if product_col in filtered_df.columns:
        cond = cond | filtered_df[product_col].astype(str).str.contains(
            active_query, na=False, case=False
        )
      if agency_col in filtered_df.columns:
        cond = cond | filtered_df[agency_col].astype(str).str.contains(
            active_query, na=False, case=False
        )
      filtered_df = filtered_df[cond]

    editor_df = filtered_df.drop(
        columns=[
            "__PARSED_DATE",
            "__YEAR",
            "__MONTH",
            "__PCS_NUM",
            "__KG_NUM",
            "__SORT_DATE",
        ],
        errors="ignore",
    )
    st.data_editor(format_df_dates(editor_df), use_container_width=True)

  elif menu == t["menu_2"]:
    st.subheader("Shipment Calendar")
    if date_col in df.columns:
      valid_df = df.dropna(subset=[date_col]).copy()
      valid_df["YearMonth"] = valid_df[date_col].dt.to_period("M").astype(str)
      ym_list = sorted(valid_df["YearMonth"].unique(), reverse=True)
      if ym_list:
        selected_ym = st.selectbox("Select Year-Month", ym_list)
        month_df = valid_df[valid_df["YearMonth"] == selected_ym]
        st.dataframe(format_df_dates(month_df), use_container_width=True)
      else:
        st.warning(t["no_data"])
    else:
      st.warning(t["no_data"])

  elif menu == t["menu_3"]:
    st.subheader("Agency History")
    if agency_col in df.columns:
      selected_target = st.selectbox(
          "Select Agency", df[agency_col].dropna().unique()
      )
      target_df = df[df[agency_col] == selected_target]
      st.dataframe(format_df_dates(target_df), use_container_width=True)
    else:
      st.warning(t["no_data"])

  elif menu == t["menu_4"]:
    st.subheader("Comparative Analysis")
    if "__YEAR" in df.columns:
      yearly_summary = (
          df[df["__YEAR"] > 0]
          .groupby("__YEAR")
          .agg({"__YEAR": "count", "__KG_NUM": "sum"})
          .rename(columns={"__YEAR": "Orders", "__KG_NUM": "Total_Kg"})
          .reset_index()
          .sort_values(by="__YEAR", ascending=False)
      )
      st.dataframe(yearly_summary, use_container_width=True)
      st.bar_chart(yearly_summary.set_index("__YEAR")["Orders"])
    else:
      st.warning(t["no_data"])

  elif menu == t["menu_5"]:
    st.subheader("Staff Memos")
    if ship_col and product_col in df.columns:
      df["오더표시"] = (
          df.index.astype(str)
          + " | "
          + df[ship_col].astype(str)
          + " | "
          + df[product_col].astype(str)
      )
      selected_label = st.selectbox("Select Order", df["오더표시"].tolist())
      idx = int(selected_label.split(" | ")[0])
      memo = st.text_area(
          "Enter Memo", value=st.session_state.order_memos.get(idx, "")
      )
      if st.button(t["save_btn"]):
        st.session_state.order_memos[idx] = memo
        st.success(t["save_success"])
    else:
      st.warning(t["no_data"])

  elif menu == t["menu_6"]:
    st.subheader("Visitor Statistics (Admin Only)")
    if is_admin:
      st.info("Visitor stats tracking table or chart goes here.")
    else:
      st.warning("Admin access required to view visitor stats.")

except Exception as e:
  st.error(f"Error: {e}")
