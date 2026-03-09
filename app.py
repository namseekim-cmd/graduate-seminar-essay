import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 보안 및 UI 최적화
# ==========================================
st.set_page_config(page_title="2026 대학원 세미나 토론장", page_icon="💬", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #f0f2f6; border-radius: 5px; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #1A237E; color: white; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 구글 시트 연결
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ 연결 오류: {e}")
    st.stop()

# ==========================================
# 3. 데이터 로드 및 탭 구성
# ==========================================
st.title("🎓 2026 대학원 세미나: 공유와 토론")

selected_week = st.selectbox("📅 주차를 선택하세요", [f"Week{i:02d}" for i in range(1, 14)])

# 에세이 데이터와 댓글 데이터를 각각 관리합니다.
try:
    df = conn.read(worksheet=selected_week, ttl=0)
    # 댓글 저장을 위한 별도의 시트 'Comments'가 필요합니다.
    comment_df = conn.read(worksheet="Comments", ttl=0)
except:
    df = pd.DataFrame(columns=["학번", "이름", "글자수", "제출시간", "내용"])
    comment_df = pd.DataFrame(columns=["Week", "TargetID", "Author", "Text", "Time"])

tab1, tab2 = st.tabs(["📝 에세이 제출", "📖 함께 읽기 & 비평"])

# ==========================================
# 4. [탭 1] 에세이 제출 (기존 기능)
# ==========================================
with tab1:
    with st.form("submit_form", clear_on_submit=True):
        st.info(f"📍 {selected_week} 에세이 제출란 (1,500자 이상)")
        c_id, c_name = st.columns(2)
        sid = c_id.text_input("학번")
        sname = c_name.text_input("성함")
        content = st.text_area("에세이 내용", height=500)
        submitted = st.form_submit_button("🚀 제출하기")

        if submitted:
            if not sid or not sname: st.warning("정보를 입력하세요.")
            elif len(content) < 1500: st.error(f"글자수 부족 ({len(content)}자)")
            elif sid in df['학번'].astype(str).values: st.error("이미 제출되었습니다.")
            else:
                new_data = pd.DataFrame([{"학번": str(sid), "이름": str(sname), "글자수": len(content), 
                                          "제출시간": datetime.now().strftime('%Y-%m-%d %H:%M'), "내용": content}])
                updated_df = pd.concat([df, new_data], ignore_index=True).astype(str)
                conn.update(worksheet=selected_week, data=updated_df)
                st.balloons()
                st.success("제출 완료!")
                st.rerun()

# ==========================================
# 5. [탭 2] 함께 읽기 & 댓글 달기
# ==========================================
with tab2:
    if df.empty:
        st.info("아직 제출된 에세이가 없습니다.")
    else:
        st.subheader(f"📑 {selected_week} 동료 에세이 목록")
        
        # 읽을 에세이 선택
        student_list = [f"{row['학번']} {row['이름']}" for _, row in df.iterrows()]
        target_student = st.selectbox("읽어볼 동료를 선택하세요", student_list)
        
        target_id = target_student.split()[0]
        essay_row = df[df['학번'] == target_id].iloc[0]
        
        # 에세이 본문 출력
        st.markdown(f"### 🖋️ {essay_row['이름']} 선생님의 글")
        st.write(f"⏱️ 제출시간: {essay_row['제출시간']} | 📏 글자수: {essay_row['글자수']}자")
        st.info(essay_row['내용'])
        
        st.divider()
        
        # 댓글 표시 및 작성 섹션
        st.subheader("💬 동료 비평 (Comments)")
        
        # 현재 에세이에 달린 댓글 필터링
        this_comments = comment_df[(comment_df['Week'] == selected_week) & (comment_df['TargetID'] == target_id)]
        
        if not this_comments.empty:
            for _, c in this_comments.iterrows():
                with st.chat_message("user"):
                    st.write(f"**{c['Author']}**: {c['Text']}")
                    st.caption(f"at {c['Time']}")
        else:
            st.caption("첫 번째 코멘트를 남겨보세요.")

        # 댓글 작성 폼
        with st.form("comment_form", clear_on_submit=True):
            c_author = st.text_input("내 이름")
            c_text = st.text_area("코멘트 내용 (비판적이고 건설적인 의견을 남겨주세요)")
            c_submit = st.form_submit_button("💭 코멘트 등록")
            
            if c_submit:
                if c_author and c_text:
                    new_comment = pd.DataFrame([{"Week": selected_week, "TargetID": target_id, 
                                                 "Author": c_author, "Text": c_text, 
                                                 "Time": datetime.now().strftime('%m-%d %H:%M')}])
                    updated_comment_df = pd.concat([comment_df, new_comment], ignore_index=True).astype(str)
                    conn.update(worksheet="Comments", data=updated_comment_df)
                    st.success("코멘트가 등록되었습니다.")
                    st.rerun()
                else:
                    st.warning("이름과 내용을 입력하세요.")
