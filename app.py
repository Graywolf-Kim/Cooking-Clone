import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import urllib.parse
import re

# 1. API 키 설정 (Secrets 사용)
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = ""

# 2. 디자인 설정 (공백 최소화 및 여백 조정)
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")
st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; margin-bottom: 5px; }
    
    /* 상단 안내문 박스 (공백을 확 줄였습니다) */
    .intro-box { 
        background-color: rgba(255, 255, 255, 0.5); padding: 20px 25px; 
        border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.5; 
        margin-top: 10px; margin-bottom: 15px; 
    }
    
    .shop-btn { 
        display: inline-block; padding: 6px 14px; margin: 4px; 
        background-color: white; border: 1px solid #5f0080; 
        border-radius: 20px; font-size: 0.85em; text-decoration: none !important; 
        color: #5f0080 !important; font-weight: bold; 
    }
    .shop-btn:hover { background-color: #5f0080; color: white !important; }
    
    .stButton>button { 
        background-color: #556B2F; color: white; border-radius: 8px; 
        width: 100%; height: 3.5em; font-weight: bold; margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 메인 UI (불필요한 줄바꿈 제거)
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 영원한 레시피가 됩니다."**')

st.markdown("""
<div class="intro-box">
    <h4 style="color: #36454F; margin-top: 0; margin-bottom: 10px;">맛있는 요리를 발견하셨나요? 지금 바로 사진을 업로드해 보세요!</h4>
    <p style="font-size: 1.0em; color: #4F4F4F; margin-bottom: 15px;"><b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독하여 조리법을 제공해 드립니다.</p>
    <div style="font-size: 0.95em;">
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">🔍</span> <b>역설계:</b> 재료와 조리 방식을 정밀하게 뽑아내어 쉽게 설명합니다.</div>
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">✨</span> <b>비법:</b> 식당 맛을 내는 결정적 포인트와 비결을 제공합니다.</div>
        <div><span style="font-size: 1.1em;">🏠</span> <b>가이드:</b> 가정에 있는 조리 도구에 최적화된 방법을 제시합니다.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. 분석 로직
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    source = st.file_uploader("사진을 선택하세요", type=["jpg", "png", "jpeg"])
    
    if source:
        img = Image.open(source)
        st.image(img, use_container_width=True)
        if st.button("✨ 비법 복제하기"):
            with st.spinner("미식 데이터를 해독 중입니다..."):
                prompt = "당신은 미식 가이드 '쿠킹클론'입니다. 요리 분석, 비법, 역설계 재료, 홈스타일 레시피 순으로 작성하세요. 마지막에 [Ingredients: 재료1, 재료2, 재료3, 재료4, 재료5] 형식을 꼭 포함하세요."
                res = model.generate_content([prompt, img])
                
                # 기호 오류 방지를 위한 텍스트 세탁
                clean_text = re.sub(r'```[a-zA-Z]*\n', '', res.text)
                clean_text = clean_text.replace('```', '')
                
                # 핵심 해결: HTML 박스로 감싸지 않고 순수 텍스트로 출력하여 글씨체(굵기, 제목 등)를 살립니다.
                st.markdown("---")
                st.markdown(clean_text)
                st.markdown("---")
                
                if "[Ingredients:" in clean_text:
                    try:
                        ings = clean_text.split("[Ingredients:")[1].split("]")[0].split(",")
                        st.markdown("#### 🛒 추천 신선 재료 (마켓컬리)")
                        links = "".join([f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(i.strip())}" target="_blank" class="shop-btn">💜 {i.strip()} 컬리 장보기</a>' for i in ings[:5]])
                        st.markdown(f'<div style="text-align:center;">{links}</div>', unsafe_allow_html=True)
                    except:
                        pass
else:
    st.warning("Secrets 설정에서 API_KEY를 입력해 주세요.")
