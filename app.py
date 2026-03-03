import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re

# 1. API 키 설정
try:
    API_KEY = st.secrets["API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("Streamlit Secrets에 API_KEY가 없습니다. 톱니바퀴 > Secrets를 확인해주세요.")

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

def make_kurly_link(match):
    keyword = urllib.parse.quote(match.group(1).strip())
    return f'<a href="https://www.kurly.com/search?keyword={keyword}" target="_blank" class="shop-btn">장보기</a>'

st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다."**')

st.markdown("""
<div class="intro-box">
    <h4 style="color: #36454F; margin-top: 0; margin-bottom: 10px;">맛있는 요리를 발견하셨나요? 지금 바로 사진을 찍어보세요!</h4>
    <p style="font-size: 1.0em; color: #4F4F4F; margin-bottom: 15px;"><b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독하여 조리법을 제공해 드립니다.</p>
    <div style="font-size: 0.95em;">
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">🔍</span> <b>역설계:</b> 재료와 조리 방식을 정밀하게 추출합니다.</div>
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">✨</span> <b>비법:</b> 식당 맛을 내는 핵심 비결을 공개합니다.</div>
        <div><span style="font-size: 1.1em;">🏠</span> <b>가이드:</b> 가정용 조리 도구에 최적화된 레시피로 변환합니다.</div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
source = None
with tab1: cam_source = st.camera_input("요리 사진 촬영")
with tab2: file_source = st.file_uploader("이미지 파일 선택", type=["jpg", "png", "jpeg"])
source = cam_source if cam_source else file_source

if source:
    img = Image.open(source)
    st.image(img, use_container_width=True)
    
    # 가장 빠르고 안정적인 최신 모델 명시
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.spinner("✨ 비법 복제 중... 잠시만 기다려주세요."):
        prompt = """
        당신은 미식 평론가 '쿠킹클론'입니다. 아래 양식으로 답변하세요.
        ### 요리분석 : (강렬한 1문장)
        ### 한끗차이 : (핵심 비결 1문장)
        ### 역설계 재료 (2인분 기준) : (재료 정량 표기, 끝에 %KURLY_LINK_재료명% 포함)
        ### 홈스타일 레시피 : (번호 매긴 과정)
        """
        
        report_placeholder = st.empty()
        full_text = ""
        
        try:
            response = model.generate_content([prompt, img], stream=True)
            for chunk in response:
                full_text += chunk.text
                clean_text = full_text.replace("```markdown", "").replace("```html", "").replace("```", "")
                report_placeholder.markdown(f"---\n{clean_text}")
            
            display_html = re.sub(r'%KURLY_LINK_(.*?)%', make_kurly_link, clean_text)
            report_placeholder.markdown(f"---\n{display_html}\n---", unsafe_allow_html=True)
            
            st.download_button("📄 레시피 리포트 저장 (PDF용)", data=display_html, file_name="recipe.html", mime="text/html")
            
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
