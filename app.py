import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re
import uuid
from datetime import datetime

# 1. 환경 설정 및 익명 세션 ID 생성
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())[:8]

USER_ID = st.session_state['user_id']

# API 키 설정 (Streamlit Secrets 필수)
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = ""

# 2. 디자인 및 CSS (만개의 레시피 스타일 장보기 반영)
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")
st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; }
    .intro-box { background-color: rgba(255, 255, 255, 0.5); padding: 20px 25px; border-radius: 15px; border-left: 8px solid #556B2F; margin-bottom: 20px; }
    .shop-btn { 
        float: right; padding: 2px 8px; background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; 
        font-size: 0.72em; text-decoration: none !important; color: #999 !important; margin-top: 4px;
    }
    .shop-btn:hover { border-color: #ccc; color: #556B2F !important; background-color: #f0f0f0; }
    li { clear: both; line-height: 1.8; margin-bottom: 6px; list-style-type: none; border-bottom: 1px dotted #ccc; padding-bottom: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 메인 화면 구성
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다."**')

st.markdown(f"""
<div class="intro-box">
    <p style="font-size: 0.9em; color: #666; float: right;">Session: {USER_ID}</p>
    <p>사진을 업로드하면 <b>역설계 레시피</b>와 <b>비법</b>을 해독해 드립니다.</p>
</div>
""", unsafe_allow_html=True)

# 4. 분석 엔진 초기화
@st.cache_resource
def load_model(api_key):
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_model(API_KEY)

# 5. 이미지 입력 및 실행
tab1, tab2 = st.tabs(["📸 촬영", "📁 업로드"])
source = None
with tab1: cam_source = st.camera_input("요리 촬영")
with tab2: file_source = st.file_uploader("파일 선택", type=["jpg", "png", "jpeg"])

source = cam_source if cam_source else file_source

if source:
    img = Image.open(source)
    st.image(img, use_container_width=True)
    
    if not API_KEY:
        st.error("설정에서 API_KEY를 등록해주세요.")
    else:
        with st.spinner("✨ 비법 복제 중..."):
            # 프롬프트 설계 (요구사항 반영)
            prompt = """
            당신은 미식 평론가 '쿠킹클론'입니다. 아래 양식으로만 답변하세요.
            ### 요리분석 : (강렬한 1문장)
            ### 한끗차이 : (핵심 비결 1문장)
            ### 역설계 재료 (2인분 기준) : (재료명과 정량화된 양, 끝에 %KURLY_LINK_재료명% 포함)
            ### 홈스타일 레시피 : (번호 매긴 요약 과정)
            """
            try:
                response = model.generate_content([prompt, img])
                res_text = response.text
                
                # 장보기 버튼 치환 로직
                display_html = re.sub(
                    r'%KURLY_LINK_(.*?)%', 
                    lambda m: f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(m.group(1).strip())}" target="_blank" class="shop-btn">장보기</a>', 
                    res_text
                )
                
                st.markdown("---")
                st.markdown(display_html, unsafe_allow_html=True)
                st.markdown("---")
                
                # 리포트 다운로드
                st.download_button("📄 레시피 리포트 저장", data=display_html, file_name="recipe.html", mime="text/html")
                st.caption("※ 본 레시피는 AI 역설계 기반이며, 실제 매장과 차이가 있을 수 있습니다.")
                
            except Exception as e:
                st.error(f"분석 실패: {e}")
