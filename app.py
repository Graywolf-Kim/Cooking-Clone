import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import threading

# 1. 초기 설정 (익명 ID 유지)
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())[:8]
USER_ID = st.session_state['user_id']

# API 및 DB 연결 설정
API_KEY = st.secrets.get("API_KEY", "")
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

# 2. 백그라운드 로깅 함수 (사용자 대기시간 0초)
def log_to_sheets_background(dish_name, action, item=""):
    """메인 화면과 분리되어 뒷단에서 조용히 실행되는 함수입니다."""
    if conn is None: return
    try:
        log_data = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": USER_ID,
            "dish_name": dish_name,
            "action": action,
            "item": item
        }])
        existing = conn.read(worksheet="Sheet1")
        updated = pd.concat([existing, log_data], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated)
    except Exception as e:
        print(f"Background Logging Error: {e}")

def fire_and_forget_log(dish_name, action):
    """백그라운드 기록을 지시하는 스위치"""
    threading.Thread(target=log_to_sheets_background, args=(dish_name, action)).start()

# 3. 디자인 설정
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

# 4. 인트로 섹션 (앱 실행 즉시 노출 유지)
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

# 5. 이미지 입력
tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
source = None
with tab1: cam_source = st.camera_input("요리 사진 촬영")
with tab2: file_source = st.file_uploader("이미지 파일 선택", type=["jpg", "png", "jpeg"])
source = cam_source if cam_source else file_source

# 6. 메인 로직 (스트리밍 + 백그라운드 기록)
if source:
    img = Image.open(source)
    st.image(img, use_container_width=True)
    
    if not API_KEY:
        st.warning("Secrets 설정에서 API_KEY를 등록해 주세요.")
    else:
        model = genai.GenerativeModel('gemini-1.5-flash')
        with st.spinner("✨ 비법 복제 중... 잠시만 기다려주세요."):
            prompt = """
            당신은 미식 평론가
