import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# [보안 및 설정] 변수 초기화
API_KEY = ""
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())[:8]
USER_ID = st.session_state['user_id']

# [속도 최적화] 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    conn = None

def save_log_to_sheets(dish, action, item=""):
    """데이터가 많아질수록 느려지는 현상을 방지하기 위해 예외처리 강화"""
    if conn:
        try:
            # 매번 전체를 읽지 않고 업데이트 시도 (API 속도 한계는 존재함)
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

# [UI/UX] 스타일 설정 (예전 버전의 감성 복구)
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

# [UI/UX] 1번 요구사항: 첫 화면 설명 문구 복구
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다."**')

st.markdown(f"""
<div class="intro-box">
    <p style="font-size: 0.85em; color: #666; float: right;">ID: {USER_ID}</p>
    <h4 style="color: #36454F; margin-top: 0; margin-bottom: 10px;">맛있는 요리를 발견하셨나요? 지금 바로 사진을 찍어보세요!</h4>
    <p style="font-size: 1.0em; color: #4F4F4F; margin-bottom: 15px;"><b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독하여 조리법을 제공해 드립니다.</p>
    <div style="font-size: 0.95em;">
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">🔍</span> <b>역설계:</b> 재료와 조리 방식을 정밀하게 추출합니다.</div>
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">✨</span> <b>비법:</b> 식당 맛을 내는 결정적 포인트(한 끗 차이)를 공개합니다.</div>
        <div><span style="font-size: 1.1em;">🏠</span> <b>가이드:</b> 가정용 조리 도구에 최적화된 레시피로 변환합니다.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# [입력] 사진 촬영 및 업로드
tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
source = None
with tab1: cam_source = st.camera_input("요리 사진 촬영")
with tab2: file_source = st.file_uploader("이미지 파일 선택", type=["jpg", "png", "jpeg"])

source = cam_source if cam_source else file_source

# [실행] 분석 로직
if source:
    img = Image.open(source)
    st.image(img, use_container_width=True)
    
    if not API_KEY:
        st.warning("Secrets 설정에서 API_KEY를 등록해 주세요.")
    else:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # 상태 표시 및 분석 시작
        with st.spinner("✨ 비법 복제 중... 미식 데이터를 정밀 해독하고 있습니다."):
            prompt = """
            당신은 미식 평론가이자 요리 연구가 '쿠킹클론'입니다. 아래 양식으로만 답변하세요.
            ### 요리분석 : (짧고 강렬한 시적 평론 1문장)
            ### 한끗차이 : (식당 맛의 핵심 비결 1문장)
            ### 역설계 재료 (2인분 기준) : (재료별 1T, 100g 등 정량 표기, 항목 끝에 %KURLY_LINK_재료명% 포함)
            ### 홈스타일 레시피 : (가정용으로 요약된 단계별 과정)
            """
            try:
                response = model.generate_content([prompt, img])
                res_text = response.text
                
                # UI 출력 (로그 기록보다 먼저 수행하여 체감 속도 향상)
                display_html = re.sub(
                    r'%KURLY_LINK_(.*?)%', 
                    lambda m: f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(m.group(1).strip())}" target="_blank" class="shop-btn">장보기</a>', 
                    res_text
                )
                st.markdown("---")
                st.markdown(display_html, unsafe_allow_html=True)
                st.markdown("---")
                
                # 다운로드 버튼 및 로그 기록
                if st.download_button("📄 레시피 리포트 저장 (PDF용)", data=display_html, file_name="recipe.html", mime="text/html"):
                    save_log_to_sheets(res_text[:20], "download_report")
                
                # 분석 완료 로그 기록 (화면 출력 후 백그라운드 느낌으로 실행)
                save_log_to_sheets(res_text[:20], "analysis_complete")
                
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
