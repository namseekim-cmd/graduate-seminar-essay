import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 보안 및 UI 최적화
# ==========================================
st.set_page_config(page_title="2026 대학원 세미나 에세이", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main .block-container {padding-top: 2rem;}
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1A237E;
        color: white;
        font-weight: bold;
        height: 3.5em;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 구글 시트 연결
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ 연결 오류: Secrets 설정을 확인하세요. ({e})")
    st.stop()

# ==========================================
# 3. 상단부: 주차 선택 및 현황판
# ==========================================
st.title("🎓 2026 예술학 기초 : 에세이 제출")
st.markdown("##### 온라인 과제 관리 시스템")

# 주차 선택 (본문 상단)
selected_week = st.selectbox(
    "📅 현재 제출 및 확인하려는 주차를 선택하세요", 
    [f"Week{i:02d}" for i in range(1, 14)]
)

try:
    df = conn.read(worksheet=selected_week, ttl=0)
except:
    df = pd.DataFrame(columns=["학번", "이름", "글자수", "제출시간", "내용"])

st.divider()

# 대시보드
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("현재 제출 인원", f"{len(df)} / 23명")
with c2:
    remaining = 23 - len(df)
    st.metric("미제출 인원", f"{max(0, remaining)}명")
with c3:
    avg_len = int(df['글자수'].astype(int).mean()) if not df.empty else 0
    st.metric("평균 글자수", f"{avg_len}자")

# ==========================================
# 4. 에세이 제출 폼 (기한 제한 없음)
# ==========================================
st.divider()

# 요일 제한 로직(is_open)을 삭제하여 항상 아래 폼이 나타납니다.
with st.form("essay_form", clear_on_submit=True):
    st.success(f"📍 **[{selected_week}]** 과제를 작성 중입니다. (1,500자 이상)")
    
    col_id, col_name = st.columns(2)
    with col_id: sid = st.text_input("학번", placeholder="학번을 입력하세요")
    with col_name: sname = st.text_input("성함", placeholder="이름을 입력하세요")
    
    content = st.text_area(
        "에세이 내용", 
        height=600,
        placeholder="강독 텍스트 내용을 바탕으로 본인의 생각을 1,500자 이상 서술하세요."
    )
    
    submitted = st.form_submit_button(f"🚀 {selected_week} 에세이 최종 제출")

    if submitted:
        if not sid or not sname:
            st.warning("학번과 성함을 입력해 주세요.")
        elif len(content) < 1500:
            st.error(f"❌ 제출 불가: 현재 {len(content)}자입니다. (최소 1,500자 이상 작성 필수)")
        elif sid in df['학번'].astype(str).values:
            st.error(f"❌ 중복 제출: 해당 주차에 이미 제출된 기록이 있습니다.")
        else:
            with st.spinner("데이터를 안전하게 저장하고 있습니다..."):
                try:
                    new_data = pd.DataFrame([{
                        "학번": str(sid),
                        "이름": str(sname),
                        "글자수": len(content),
                        "제출시간": datetime.now().strftime('%Y-%m-%d %H:%M'),
                        "내용": content
                    }])

                    updated_df = pd.concat([df, new_data], ignore_index=True).astype(str)
                    conn.update(worksheet=selected_week, data=updated_df)
                    
                    st.balloons()
                    st.success(f"✅ {sname} 선생님, 제출이 완료되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 시스템 오류: {e}")

# ==========================================
# 5. 관리 및 명단 확인
# ==========================================
st.divider()

with st.expander("🛠️ 시스템 관리"):
    pw = st.text_input("관리자 인증", type="password")
    if pw == "1234":
        if st.button(f"🔥 {selected_week} 데이터 전체 초기화"):
            empty_df = pd.DataFrame(columns=["학번", "이름", "글자수", "제출시간", "내용"])
            conn.update(worksheet=selected_week, data=empty_df)
            st.success("데이터가 삭제되었습니다.")
            st.rerun()

if not df.empty:
    with st.expander("📋 제출 확인 명단"):
        # 명단에서는 에세이 본문(내용)을 제외하고 요약 정보만 표시
        show_cols = ["학번", "이름", "글자수", "제출시간"]
        st.dataframe(df[show_cols].iloc[::-1], use_container_width=True)


