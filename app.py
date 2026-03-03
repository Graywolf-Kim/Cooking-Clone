import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# [핵심 수정] 변수 초기화 - NameError 방지
API_KEY = "" 
USER_ID = ""

# 1. 익명 세션 ID 관리
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())[:8]
USER_ID = st.session_state['user_id']

# 2. 구글 시트 연결 설정
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    conn = None

def save_log_to_sheets(dish, action, item=""):
    """구글 시트에 로그 기록"""
    if conn:
        try:
            new_entry = pd.DataFrame([{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": USER_ID,
                "dish_name": dish,
                "action": action,
                "item": item
            }])
            existing_data = conn.read(worksheet="Sheet1")
            updated_data = pd.concat([existing_data, new_entry], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_data)
        except:
            pass

# 3. API 키 로드 (NameError 방지를 위해 확실히 정의)
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]

# 디자인 설정 (최신 버전 유지)
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")
st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; }
    .shop-btn { 
        float: right; padding: 2px 8px; background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; 
        font-size: 0.72em; text-decoration: none !important; color: #999 !important; 
    }
    li { clear: both; line-height: 1.8; margin-bottom: 6px; border-bottom: 1px dotted #ccc; padding-bottom: 4px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍳 쿠킹클론 (Cooking Clone)")
st.caption(f"익명 ID: {USER_ID}")

# 4. 이미지 입력 탭
tab1, tab2 = st.tabs(["📸 촬영", "📁 업로드"])
source = None
with tab1: cam_source = st.camera_input("요리 촬영")
with tab2: file_source = st.file_uploader("파일 선택", type=["jpg", "png", "jpeg"])

source = cam_source if cam_source else file_source

# 5. 실행 로직 (문제의 61번 줄 보강)
if source:
    img = Image.open(source)
    st.image(img, use_container_width=True)
    
    if not API_KEY:
        st.warning("Secrets 설정에서 API_KEY를 등록해 주세요.")
    else:
        model = genai.GenerativeModel('gemini-1.5-flash')
        with st.spinner("✨ 미식 데이터 해독 및 기록 중..."):
            prompt = """
            당신은 미식 평론가 '쿠킹클론'입니다. 아래 양식으로 답변하세요.
            ### 요리분석 : (강렬한 1문장)
            ### 한끗차이 : (핵심 비결 1문장)
            ### 역설계 재료 (2인분 기준) : (재료명과 정량화된 양, 끝에 %KURLY_LINK_재료명% 포함)
            ### 홈스타일 레시피 : (번호 매긴 요약 과정)
            """
            try:
                response = model.generate_content([prompt, img])
                res_text = response.text
                
                # 로그 저장
                dish_preview = res_text.split('\n')[0][:20]
                save_log_to_sheets(dish_preview, "analysis_complete")
                
                # 결과 출력
                display_html = re.sub(
                    r'%KURLY_LINK_(.*?)%', 
                    lambda m: f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(m.group(1).strip())}" target="_blank" class="shop-btn">장보기</a>', 
                    res_text
                )
                st.markdown("---")
                st.markdown(display_html, unsafe_allow_html=True)
                
                if st.download_button("📄 레시피 저장", data=display_html, file_name="recipe.html"):
                    save_log_to_sheets(dish_preview, "download_report")
                    
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
