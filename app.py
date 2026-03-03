import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 초기 설정 (익명 ID)
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())[:8]
USER_ID = st.session_state['user_id']

# API 키 및 구글 시트 연결
API_KEY = st.secrets.get("API_KEY", "")
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    conn = None

# 2. 디자인 설정 (인트로 박스 감성 복구)
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")
st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; margin-bottom: 5px; }
    .intro-box { background-color: rgba(255, 255, 255, 0.5); padding: 20px 25px; border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.5; margin-top: 10px; margin-bottom: 20px; }
    .shop-btn { float: right; padding: 2px 8px; background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 0.72em; text-decoration: none !important; color: #999 !important; }
    li { clear: both; line-height: 1.8; margin-bottom: 6px; border-bottom: 1px dotted #ccc; padding-bottom: 4px; list-style: none; }
    </style>
    """, unsafe_allow_html=True)

# 3. 인트로 섹션 (기존 버전 유지)
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다."**')
st.markdown(f"""
<div class="intro-box">
    <p style="font-size: 0.85em; color: #666; float: right;">ID: {USER_ID}</p>
    <h4 style="color: #36454F; margin-top: 0; margin-bottom: 10px;">맛있는 요리를 발견하셨나요? 지금 바로 사진을 찍어보세요!</h4>
    <p style="font-size: 1.0em; color: #4F4F4F; margin-bottom: 15px;"><b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독하여 조리법을 제공해 드립니다.</p>
    <div style="font-size: 0.95em;">
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">🔍</span> <b>역설계:</b> 재료와 조리 방식을 정밀하게 추출합니다.</div>
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">✨</span> <b>비법:</b> 식당 맛을 내는 핵심 비결을 공개합니다.</div>
        <div><span style="font-size: 1.1em;">🏠</span> <b>가이드:</b> 가정용 조리 도구에 최적화된 레시피로 변환합니다.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. 사진 입력
tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
source = None
with tab1: cam_source = st.camera_input("요리 촬영")
with tab2: file_source = st.file_uploader("파일 선택", type=["jpg", "png", "jpeg"])
source = cam_source if cam_source else file_source

# 5. 메인 로직 (속도 최적화: UI 우선 로드)
if source:
    img = Image.open(source)
    st.image(img, use_container_width=True)
    
    if not API_KEY:
        st.warning("Secrets 설정에서 API_KEY를 등록해 주세요.")
    else:
        # [핵심] 스피너 안에는 AI 분석만 넣습니다. (시트 기록 제외)
        with st.spinner("✨ 미식 데이터 해독 중... 잠시만 기다려주세요."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = "당신은 미식 평론가 '쿠킹클론'입니다. 요리분석, 한끗차이, 역설계 재료(2인분 정량, %KURLY_LINK_재료명% 포함), 홈스타일 레시피 순으로 답변하세요."
            try:
                response = model.generate_content([prompt, img])
                res_text = response.text
                
                # 결과 즉시 출력 (사용자가 기다리지 않게 함)
                display_html = re.sub(
                    r'%KURLY_LINK_(.*?)%', 
                    lambda m: f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(m.group(1).strip())}" target="_blank" class="shop-btn">장보기</a>', 
                    res_text
                )
                st.markdown("---")
                st.markdown(display_html, unsafe_allow_html=True)
                st.markdown("---")
                
                # 리포트 저장 버튼
                btn_placeholder = st.empty()
                if btn_placeholder.download_button("📄 레시피 리포트 저장 (PDF용)", data=display_html, file_name="recipe.html", mime="text/html"):
                    # 버튼 클릭 시에만 로그 기록 시도 (성능 최적화)
                    if conn:
                        log_df = pd.DataFrame([{"timestamp": datetime.now(), "user_id": USER_ID, "action": "download"}])
                        conn.update(worksheet="Sheet1", data=log_df)

            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")

        # [사후 처리] 모든 UI가 출력된 후, 코드의 맨 마지막에서 조용히 기록 시도
        if conn and 'res_text' in locals():
            try:
                log_data = pd.DataFrame([{
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_id": USER_ID,
                    "dish_name": res_text[:30],
                    "action": "analysis_view",
                    "item": ""
                }])
                # 시트의 기존 데이터를 유지하며 업데이트
                existing = conn.read(worksheet="Sheet1")
                updated = pd.concat([existing, log_data], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated)
            except:
                pass # 기록이 느려지거나 실패해도 사용자는 알 수 없음
