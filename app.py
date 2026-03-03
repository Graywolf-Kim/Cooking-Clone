import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection # 라이브러리 추가 필요

# 1. 익명 세션 ID 생성
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())[:8]
USER_ID = st.session_state['user_id']

# 2. 구글 시트 연결 설정 (Secrets에 GSheets 설정이 되어 있어야 함)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    conn = None

def save_log(dish, action, item=""):
    """구글 시트에 유저 행동 로그를 익명으로 저장"""
    if conn:
        new_log = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": USER_ID,
            "dish_name": dish,
            "action": action,
            "item": item
        }
        # 구글 시트의 기존 데이터에 한 줄 추가 (내부적으로 gspread 등 사용)
        # 실제 운영 시에는 st.cache_data.clear() 등을 조합하여 성능 최적화 가능
        try:
            conn.create(data=new_log) 
        except:
            pass # 실패 시 서비스에 지장 없도록 처리

# 3. 디자인 및 API 설정
try: API_KEY = st.secrets["API_KEY"]
except: API_KEY = ""

st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")
st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; }
    .shop-btn { 
        float: right; padding: 2px 8px; background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; 
        font-size: 0.72em; text-decoration: none !important; color: #999 !important; 
    }
    li { clear: both; line-height: 1.8; margin-bottom: 6px; border-bottom: 1px dotted #ccc; }
    </style>
    """, unsafe_allow_html=True)

# 4. 메인 분석 로직
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.caption(f"익명 세션 ID: {USER_ID}")

# ... (이미지 업로드 로직 생략) ...

if API_KEY and source:
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(source)
    st.image(img, use_container_width=True)
    
    with st.spinner("✨ 미식 데이터 해독 중..."):
        prompt = "요리명, 재료(정량화), 한끗비결, 레시피를 분석해줘. 재료 끝에 %KURLY_LINK_재료명% 포함."
        response = model.generate_content([prompt, img])
        res_text = response.text
        
        # 분석 완료 로그 저장 (어떤 요리를 분석했는지)
        dish_name = res_text.split('\n')[0][:20] # 첫 줄에서 요리명 추출 시도
        save_log(dish_name, "analysis_complete")
        
        # 장보기 버튼 생성
        display_html = re.sub(
            r'%KURLY_LINK_(.*?)%', 
            lambda m: f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(m.group(1).strip())}" target="_blank" class="shop-btn">장보기</a>', 
            res_text
        )
        st.markdown(display_html, unsafe_allow_html=True)

        if st.download_button("📄 레시피 저장", data=display_html, file_name="recipe.html"):
            save_log(dish_name, "download_report")
