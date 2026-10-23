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
        "subtitle": "실시간 구글 스프레드시트 연동 및 스마트 SCM 대시보드 (MULTILINGUAL ULTIMATE)",
        "lang_select": "🌐 언어 선택 (Language)",
        "sec_menu": "🔐 보안 및 시스템 메뉴",
        "pw_label": "관리자 비밀번호 입력",
        "pw_placeholder": "관리자 전용 기능 해제",
        "admin_success": "🔓 관리자 모드가 활성화되었습니다.",
        "pw_error": "❌ 비밀번호가 틀렸습니다. (일반 조회 모드)",
        "general_info": "💡 일반 조회 모드 (검색 및 현황 확인 가능)",
        "menu_1": "📊 종합 대시보드 & 일정별 알림",
        "menu_2": "📈 통계 및 거래처 분석",
        "menu_3": "📝 실무자 메모 및 특이사항",
        "menu_4": "💬 팀즈 알림 전송",
        "total_orders": "📋 전체 수주 건수",
        "d7_imminent": "🚨 7일 이내 납기",
        "d30_expect": "📅 1달 후(30일) 예정",
        "d60_expect": "🗓️ 2달 후(60일) 예정",
        "completion_rate": "🎯 전체 출고 달성률",
        "search_box": "🔍 출하처 또는 제품명 검색",
        "agency_filter": "🏢 대리점 선택 필터",
        "date_filter": "📅 납기일 범위 직접 지정 조회",
        "excel_btn": "📥 엑셀로 다운로드",
        "memo_menu": "📝 오더별 실무자 메모 및 특이사항 관리",
        "memo_info": "💡 특정 오더에 대한 특이사항(예: 납기 연기 사유, 원단 확인 등)을 기록하고 팀원들과 공유할 수 있습니다.",
        "memo_select": "메모를 남길 오더를 선택하세요",
        "memo_input": "✍️ 특이사항 및 메모 입력",
        "memo_save": "💾 메모 저장하기",
        "memo_success": "✅ 메모가 성공적으로 저장되었습니다!",
        "memo_list": "📋 현재까지 작성된 전체 메모 목록",
        "teams_menu": "💬 마이크로소프트 팀즈 납기/출고 일정 알림 전송",
        "teams_info": "💡 팀즈 채널의 웹훅(Webhook) URL을 입력하고 버튼을 누르면, 일정별 리스트가 전송됩니다.",
        "teams_url": "🔗 팀즈 웹훅 URL (Webhook URL)",
        "teams_btn": "🚀 전체 출고 일정 리스트 팀즈 채널로 전송하기",
        "teams_success": "✅ 팀즈 채널로 전체 일정 알림이 성공적으로 전송되었습니다!",
        "stat_menu": "📈 대리점별 및 품목별 수주 분석"
    },
    "English": {
        "title": "📦 HQ Textile Order & Shipment Management System",
        "subtitle": "Real-time Google Sheets Integration & Smart SCM Dashboard (MULTILINGUAL ULTIMATE)",
        "lang_select": "🌐 Language Selection",
        "sec_menu": "🔐 Security & System Menu",
        "pw_label": "Enter Admin Password",
        "pw_placeholder": "Unlock admin features",
        "admin_success": "🔓 Admin mode activated.",
        "pw_error": "❌ Incorrect password. (General view mode)",
        "general_info": "💡 General view mode (Search & status check available)",
        "menu_1": "📊 Dashboard & Schedule Alerts",
        "menu_2": "📈 Statistics & Partner Analysis",
        "menu_3": "📝 Staff Memos & Notes",
        "menu_4": "💬 Send Teams Alert",
        "total_orders": "📋 Total Orders",
        "d7_imminent": "🚨 Due within 7 Days",
        "d30_expect": "📅 Due within 30 Days",
        "d60_expect": "🗓️ Due within 60 Days",
        "completion_rate": "🎯 Overall Shipment Rate",
        "search_box": "🔍 Search Shipment or Product",
        "agency_filter": "🏢 Agency Filter",
        "date_filter": "📅 Custom Date Range Filter",
        "excel_btn": "📥 Download Excel",
        "memo_menu": "📝 Staff Memos & Order Notes",
        "memo_info": "💡 Record notes or special issues for specific orders to share with your team.",
        "memo_select": "Select an order to add a memo",
        "memo_input": "✍️ Enter Notes / Memo",
        "memo_save": "💾 Save Memo",
        "memo_success": "✅ Memo saved successfully!",
        "memo_list": "📋 All Saved Memos",
        "teams_menu": "💬 Microsoft Teams Schedule Alert Dispatch",
        "teams_info": "💡 Enter your Teams Channel Webhook URL to dispatch schedule alerts.",
        "teams_url": "🔗 Teams Webhook URL",
        "teams_btn": "🚀 Send Full Schedule to Teams Channel",
        "teams_success": "✅ Schedule alert successfully sent to Teams channel!",
        "stat_menu": "📈 Order Analysis by Agency & Item"
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
    agency_col = find_col(['대리점', 'AGENCY'])
    ship_col = find_col(['출하처', 'SHIPMENT'])
    product_col = find_col(['제품명', 'KOREAN NAME'])
    completed_col = find_col(['출고 완료', '출고완료'])

    if 'order_memos' not in st.session_state:
        st.session_state.order_memos = {}

    # --- 사이드바 보안 및 메뉴 설정 ---
    st.sidebar.header(t["sec_menu"])
    
    ADMIN_PASSWORD = "songwol1234" 
    
    input_pw = st.sidebar.text_input(t["pw_label"], type="password", placeholder=t["pw_placeholder"])
    is_admin = (input_pw == ADMIN_PASSWORD)
    
    if is_admin:
        st.sidebar.success(t["admin_success"])
        menu_options = [t["menu_1"], t["menu_2"], t["menu_3"], t["menu_4"]]
    else:
        if input_pw:
            st.sidebar.error(t["pw_error"])
        else:
            st.sidebar.info(t["general_info"])
        menu_options = [t["menu_1"], t["menu_2"], t["menu_3"]]

    menu = st.sidebar.radio("Menu", menu_options)

    today = pd.to_datetime(datetime.today().date())
    
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    if menu == t["menu_1"]:
        target_d7 = today + timedelta(days=7)
        target_d30 = today + timedelta(days=30)
        target_d60 = today + timedelta(days=60)

        total_len = len(df)
        completed_count = 0
        if completed_col and completed_col in df.columns:
            completed_count = len(df[df[completed_col].astype(str).str.upper() == 'O'])
        
        completion_rate = int((completed_count / total_len * 100) if total_len > 0 else 0)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label=t["total_orders"], value=f"{total_len:,}")
        
        imminent_d7 = len(df[(df[date_col] >= today) & (df[date_col] <= target_d7)]) if date_col in df.columns else 0
        with col2:
            st.metric(label=t["d7_imminent"], value=f"{imminent_d7}")
            
        imminent_d30 = len(df[(df[date_col] > target_d7) & (df[date_col] <= target_d30)]) if date_col in df.columns else 0
        with col3:
            st.metric(label=t["d30_expect"], value=f"{imminent_d30}")

        imminent_d60 = len(df[(df[date_col] > target_d30) & (df[date_col] <= target_d60)]) if date_col in df.columns else 0
        with col4:
            st.metric(label=t["d60_expect"], value=f"{imminent_d60}")

        st.markdown(f"**{t['completion_rate']}: {completion_rate}% ({completed_count} / {total_len})**")
        st.progress(completion_rate / 100.0)
            
        st.markdown("---")
        
        with st.expander(f"🚨 7 Days Imminent ({imminent_d7})", expanded=True):
            if date_col and date_col in df.columns:
                df_d7 = df[(df[date_col] >= today) & (df[date_col] <= target_d7)]
                if not df_d7.empty:
                    disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                    st.dataframe(df_d7[disp_cols], use_container_width=True)
                else:
                    st.success("No imminent orders within 7 days.")

        with st.expander(f"📅 Within 30 Days ({imminent_d30})", expanded=False):
            if date_col and date_col in df.columns:
                df_d30 = df[(df[date_col] > target_d7) & (df[date_col] <= target_d30)]
                if not df_d30.empty:
                    disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                    st.dataframe(df_d30[disp_cols], use_container_width=True)
                else:
                    st.info("No orders expected in this period.")

        with st.expander(f"🗓️ Within 60 Days ({imminent_d60})", expanded=False):
            if date_col and date_col in df.columns:
                df_d60 = df[(df[date_col] > target_d30) & (df[date_col] <= target_d60)]
                if not df_d60.empty:
                    disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                    st.dataframe(df_d60[disp_cols], use_container_width=True)
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
            use_date_filter = st.checkbox(t["date_filter"])
        
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

        col_res1, col_res2 = st.columns([3, 1])
        with col_res1:
            st.write(f"Found **{len(filtered_df):,}** orders.")
        with col_res2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Orders')
            excel_data = output.getvalue()
            st.download_button(
                label=t["excel_btn"],
                data=excel_data,
                file_name=f"Order_List_{datetime.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.dataframe(filtered_df, use_container_width=True)

    elif menu == t["menu_2"]:
        st.subheader(t["stat_menu"])
        
        col_st1, col_st2 = st.columns(2)
        
        with col_st1:
            st.markdown("### Top 10 Agencies")
            if agency_col and agency_col in df.columns:
                agency_counts = df[agency_col].value_counts().head(10)
                st.bar_chart(agency_counts)
            else:
                st.info("Agency column not found.")

        with col_st2:
            st.markdown("### Top 10 Shipments")
            if ship_col and ship_col in df.columns:
                ship_counts = df[ship_col].value_counts().head(10)
                st.bar_chart(ship_counts)
            else:
                st.info("Shipment column not found.")

        st.markdown("---")
        st.subheader("Monthly Order Receipt Analysis")
        date_rcv_col = find_col(['발주서 수령', '발주서'])
        if date_rcv_col and date_rcv_col in df.columns:
            df['수령_월'] = pd.to_datetime(df[date_rcv_col], errors='coerce').dt.to_period('M').astype(str)
            monthly_counts = df['수령_월'].value_counts().sort_index()
            st.bar_chart(monthly_counts)
        else:
            st.info("Receipt date column not found.")

    elif menu == t["menu_3"]:
        st.subheader(t["memo_menu"])
        st.info(t["memo_info"])
        
        if ship_col and product_col in df.columns:
            df['오더표시'] = df.index.astype(str) + " | Ship: " + df[ship_col].astype(str) + " | Product: " + df[product_col].astype(str)
            selected_order_label = st.selectbox(t["memo_select"], df['오더표시'].tolist())
            
            selected_idx = int(selected_order_label.split(" | ")[0])
            row_data = df.loc[selected_idx]
            
            st.write("---")
            st.markdown("#### Selected Order Details")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.write(f"**Shipment:** {row_data.get(ship_col, '')}")
            with col_m2:
                st.write(f"**Agency:** {row_data.get(agency_col, '')}")
            with col_m3:
                d_val = str(row_data.get(date_col, ''))[:10]
                st.write(f"**Delivery 1:** {d_val}")
            
            current_memo = st.session_state.order_memos.get(selected_idx, "")
            memo_input = st.text_area(t["memo_input"], value=current_memo, placeholder="e.g., Delayed due to fabric stock")
            
            if st.button(t["memo_save"]):
                st.session_state.order_memos[selected_idx] = memo_input
                st.success(t["memo_success"])
                
            st.markdown("---")
            st.markdown(f"### {t['memo_list']}")
            if st.session_state.order_memos:
                memo_list = []
                for idx, m in st.session_state.order_memos.items():
                    r = df.loc[idx]
                    memo_list.append({
                        "Index": idx,
                        "Shipment": r.get(ship_col, ''),
                        "Product": r.get(product_col, ''),
                        "Memo": m
                    })
                st.dataframe(pd.DataFrame(memo_list), use_container_width=True)
            else:
                st.info("No memos recorded yet.")
        else:
            st.warning("Required columns missing for memo feature.")

    elif menu == t["menu_4"] and is_admin:
        st.subheader(t["teams_menu"])
        st.info(t["teams_info"])
        
        with st.form("teams_form"):
            webhook_url = st.text_input(t["teams_url"], type="password", placeholder="https://outlook.office.com/webhook/...")
            submit_btn = st.form_submit_button(t["teams_btn"])
            
            if submit_btn:
                if not webhook_url:
                    st.error("Please enter the Teams Webhook URL.")
                else:
                    try:
                        if date_col and date_col in df.columns:
                            df_d7 = df[(df[date_col] >= today) & (df[date_col] <= today + timedelta(days=7))]
                            df_d30 = df[(df[date_col] > today + timedelta(days=7)) & (df[date_col] <= today + timedelta(days=30))]
                            df_d60 = df[(df[date_col] > today + timedelta(days=30)) & (df[date_col] <= today + timedelta(days=60))]
                        else:
                            df_d7, df_d30, df_d60 = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
                            
                        msg = "📦 [HQ Textile Order Schedule Report]\n\n"
                        
                        msg += f"🚨 [Imminent within 7 Days] ({len(df_d7)} orders)\n"
                        if df_d7.empty:
                            msg += "• None\n\n"
                        else:
                            for idx, row in df_d7.iterrows():
                                msg += f"• {row.get(ship_col, '')} | {row.get(product_col, '')} | {str(row.get(date_col, ''))[:10]}\n"
                            msg += "\n"

                        msg += f"📅 [Expected within 30 Days] ({len(df_d30)} orders)\n"
                        if df_d30.empty:
                            msg += "• None\n\n"
                        else:
                            for idx, row in df_d30.iterrows():
                                msg += f"• {row.get(ship_col, '')} | {row.get(product_col, '')} | {str(row.get(date_col, ''))[:10]}\n"
                            msg += "\n"

                        msg += f"🗓️ [Expected within 60 Days] ({len(df_d60)} orders)\n"
                        if df_d60.empty:
                            msg += "• None\n"
                        else:
                            for idx, row in df_d60.iterrows():
                                msg += f"• {row.get(ship_col, '')} | {row.get(product_col, '')} | {str(row.get(date_col, ''))[:10]}\n"
                        
                        payload = {
                            "type": "message",
                            "attachments": [
                                {
                                    "contentType": "application/vnd.microsoft.card.adaptive",
                                    "content": {
                                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                                        "type": "AdaptiveCard",
                                        "version": "1.2",
                                        "body": [
                                            {
                                                "type": "TextBlock",
                                                "text": msg,
                                                "wrap": True
                                            }
                                        ]
                                    }
                                }
                            ]
                        }

                        res = requests.post(webhook_url, json=payload)
                        
                        if res.status_code in [200, 202]:
                            st.success(t["teams_success"])
                        else:
                            st.error(f"❌ Failed (Error Code: {res.status_code}) - Please check your Webhook URL.")
                    except Exception as ex:
                        st.error(f"Error during transmission: {ex}")

except Exception as e:
    st.error(f"Error loading data: {e}")
