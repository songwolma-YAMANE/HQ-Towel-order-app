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

# 타이틀 디자인
st.markdown('<div class="main-header">📦 본사 문직 제품 수주 및 출고 관리 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">실시간 구글 스프레드시트 연동 및 스마트 대시보드 (UPGRADE VERSION)</div>', unsafe_allow_html=True)

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

    # --- 사이드바 보안 및 메뉴 설정 ---
    st.sidebar.header("🔐 보안 및 시스템 메뉴")
    
    ADMIN_PASSWORD = "songwol1234" 
    
    input_pw = st.sidebar.text_input("관리자 비밀번호 입력", type="password", placeholder="관리자 전용 기능 해제")
    is_admin = (input_pw == ADMIN_PASSWORD)
    
    if is_admin:
        st.sidebar.success("🔓 관리자 모드가 활성화되었습니다.")
        menu = st.sidebar.radio("메뉴 선택", ["📊 종합 대시보드 & 일정별 알림", "💬 팀즈 알림 전송", "📈 월별 수주 통계"])
    else:
        if input_pw:
            st.sidebar.error("❌ 비밀번호가 틀렸습니다. (일반 조회 모드)")
        else:
            st.sidebar.info("💡 일반 조회 모드 (검색 및 현황 확인 가능)")
        menu = st.sidebar.radio("메뉴 선택", ["📊 종합 대시보드 & 일정별 알림", "📈 월별 수주 통계"])

    today = pd.to_datetime(datetime.today().date())
    
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    if menu == "📊 종합 대시보드 & 일정별 알림":
        target_d7 = today + timedelta(days=7)
        target_d30 = today + timedelta(days=30)
        target_d60 = today + timedelta(days=60)

        # 1. 요약 지표 카드 및 출고 완료율 게이지 바 추가
        total_len = len(df)
        completed_count = 0
        if completed_col and completed_col in df.columns:
            completed_count = len(df[df[completed_col].astype(str).str.upper() == 'O'])
        
        completion_rate = int((completed_count / total_len * 100) if total_len > 0 else 0)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="📋 전체 수주 건수", value=f"{total_len:,} 건")
        
        imminent_d7 = len(df[(df[date_col] >= today) & (df[date_col] <= target_d7)]) if date_col in df.columns else 0
        with col2:
            st.metric(label="🚨 7일 이내 납기", value=f"{imminent_d7} 건")
            
        imminent_d30 = len(df[(df[date_col] > target_d7) & (df[date_col] <= target_d30)]) if date_col in df.columns else 0
        with col3:
            st.metric(label="📅 1달 후(30일) 예정", value=f"{imminent_d30} 건")

        imminent_d60 = len(df[(df[date_col] > target_d30) & (df[date_col] <= target_d60)]) if date_col in df.columns else 0
        with col4:
            st.metric(label="🗓️ 2달 후(60일) 예정", value=f"{imminent_d60} 건")

        # 전체 출고 완료율 프로그레스 바 표시
        st.markdown(f"**🎯 전체 출고 달성률: {completion_rate}% ({completed_count}건 / 총 {total_len}건 완료)**")
        st.progress(completion_rate / 100.0)
            
        st.markdown("---")
        
        # 2. 접이식 박스(Expander)를 적용한 기간별 출고 예정 리스트
        with st.expander(f"🚨 [긴급] 7일 이내 납기 임박 오더 ({imminent_d7}건)", expanded=True):
            if date_col and date_col in df.columns:
                df_d7 = df[(df[date_col] >= today) & (df[date_col] <= target_d7)]
                if not df_d7.empty:
                    disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                    st.dataframe(df_d7[disp_cols], use_container_width=True)
                else:
                    st.success("🎉 향후 7일 이내 납기가 임박한 제품이 없습니다.")

        with st.expander(f"📅 [예정] 1달 이내(8일~30일 후) 출고 예정 오더 ({imminent_d30}건)", expanded=False):
            if date_col and date_col in df.columns:
                df_d30 = df[(df[date_col] > target_d7) & (df[date_col] <= target_d30)]
                if not df_d30.empty:
                    disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                    st.dataframe(df_d30[disp_cols], use_container_width=True)
                else:
                    st.info("해당 기간 내 출고 예정인 제품이 없습니다.")

        with st.expander(f"🗓️ [계획] 2달 이내(31일~60일 후) 출고 예정 오더 ({imminent_d60}건)", expanded=False):
            if date_col and date_col in df.columns:
                df_d60 = df[(df[date_col] > target_d30) & (df[date_col] <= target_d60)]
                if not df_d60.empty:
                    disp_cols = [c for c in [ship_col, agency_col, product_col, 'ORDER PCS', date_col, completed_col] if c and c in df.columns]
                    st.dataframe(df_d60[disp_cols], use_container_width=True)
                else:
                    st.info("해당 기간 내 출고 예정인 제품이 없습니다.")
                
        st.markdown("---")
        
        # 3. 실시간 전체 오더 조회 및 엑셀 다운로드 / 날짜 범위 필터 기능 추가
        st.subheader("🔍 실시간 전체 오더 조회 및 필터링")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search_query = st.text_input("🔍 출하처 또는 제품명 검색", "")
        with col_f2:
            if agency_col and agency_col in df.columns:
                agencies = ['전체'] + list(df[agency_col].dropna().unique())
                selected_agency = st.selectbox("🏢 대리점 선택 필터", agencies)
            else:
                selected_agency = '전체'
        with col_f3:
            use_date_filter = st.checkbox("📅 납기일 범위 직접 지정 조회")
        
        filtered_df = df.copy()
        
        # 검색어 필터
        if search_query:
            cond = pd.Series(False, index=filtered_df.index)
            if ship_col and ship_col in filtered_df.columns:
                cond = cond | filtered_df[ship_col].astype(str).str.contains(search_query, na=False, case=False)
            if product_col and product_col in filtered_df.columns:
                cond = cond | filtered_df[product_col].astype(str).str.contains(search_query, na=False, case=False)
            filtered_df = filtered_df[cond]
            
        # 대리점 필터
        if selected_agency != '전체' and agency_col and agency_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[agency_col] == selected_agency]

        # 날짜 범위 필터
        if use_date_filter and date_col in filtered_df.columns:
            valid_dates = filtered_df[date_col].dropna()
            if not valid_dates.empty:
                min_d = valid_dates.min().date()
                max_d = valid_dates.max().date()
                date_range = st.date_input("조회할 납기일 범위를 선택하세요", [min_d, max_d])
                if len(date_range) == 2:
                    start_r, end_r = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                    filtered_df = filtered_df[(filtered_df[date_col] >= start_r) & (filtered_df[date_col] <= end_r)]

        # 조회 결과 건수 표시 및 엑셀 다운로드 버튼
        col_res1, col_res2 = st.columns([3, 1])
        with col_res1:
            st.write(f"총 **{len(filtered_df):,}건**의 오더가 검색되었습니다.")
        with col_res2:
            # 엑셀 다운로드 버튼 생성
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='오더조회결과')
            excel_data = output.getvalue()
            st.download_button(
                label="📥 엑셀로 다운로드",
                data=excel_data,
                file_name=f"수주출고관리_리스트_{datetime.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.dataframe(filtered_df, use_container_width=True)

    elif menu == "💬 팀즈 알림 전송" and is_admin:
        st.subheader("💬 마이크로소프트 팀즈 납기/출고 일정 알림 전송")
        st.info("💡 팀즈 채널의 **웹훅(Webhook) URL**을 입력하고 버튼을 누르면, 7일 이내 긴급 납기 건과 1달/2달 뒤 출고 예정 리스트가 팀즈 채널로 전송됩니다.")
        
        with st.form("teams_form"):
            webhook_url = st.text_input("🔗 팀즈 웹훅 URL (Webhook URL)", type="password", placeholder="https://outlook.office.com/webhook/...")
            submit_btn = st.form_submit_button("🚀 전체 출고 일정 리스트 팀즈 채널로 전송하기")
            
            if submit_btn:
                if not webhook_url:
                    st.error("팀즈 웹훅 URL을 입력해주세요.")
                else:
                    try:
                        if date_col and date_col in df.columns:
                            df_d7 = df[(df[date_col] >= today) & (df[date_col] <= today + timedelta(days=7))]
                            df_d30 = df[(df[date_col] > today + timedelta(days=7)) & (df[date_col] <= today + timedelta(days=30))]
                            df_d60 = df[(df[date_col] > today + timedelta(days=30)) & (df[date_col] <= today + timedelta(days=60))]
                        else:
                            df_d7, df_d30, df_d60 = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
                            
                        msg = "📦 [본사 문직 제품 출고 일정 종합 리스트]\n\n"
                        
                        msg += f"🚨 [7일 이내 긴급 납기] ({len(df_d7)}건)\n"
                        if df_d7.empty:
                            msg += "• 해당 없음\n\n"
                        else:
                            for idx, row in df_d7.iterrows():
                                msg += f"• {row.get(ship_col, '')} | {row.get(product_col, '')} | {str(row.get(date_col, ''))[:10]}\n"
                            msg += "\n"

                        msg += f"📅 [1달 이내 예정] ({len(df_d30)}건)\n"
                        if df_d30.empty:
                            msg += "• 해당 없음\n\n"
                        else:
                            for idx, row in df_d30.iterrows():
                                msg += f"• {row.get(ship_col, '')} | {row.get(product_col, '')} | {str(row.get(date_col, ''))[:10]}\n"
                            msg += "\n"

                        msg += f"🗓️ [2달 이내 예정] ({len(df_d60)}건)\n"
                        if df_d60.empty:
                            msg += "• 해당 없음\n"
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
                            st.success("✅ 팀즈 채널로 전체 일정 알림이 성공적으로 전송되었습니다!")
                        else:
                            st.error(f"❌ 전송 실패 (오류 코드: {res.status_code}) - 웹훅 URL을 다시 확인해주세요.")
                    except Exception as ex:
                        st.error(f"전송 중 오류 발생: {ex}")

    elif menu == "📈 월별 수주 통계":
        st.subheader("📈 월별 발주서 수령 현황 분석")
        date_rcv_col = find_col(['발주서 수령', '발주서'])
        if date_rcv_col and date_rcv_col in df.columns:
            df['수령_월'] = pd.to_datetime(df[date_rcv_col], errors='coerce').dt.to_period('M').astype(str)
            monthly_counts = df['수령_월'].value_counts().sort_index()
            st.bar_chart(monthly_counts)
        else:
            st.info("발주서 수령일 기준 통계를 생성할 수 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
