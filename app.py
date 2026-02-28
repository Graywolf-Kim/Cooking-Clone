import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import urllib.parse

# 1. API 키 설정 (Secrets 사용)
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = ""

# 2. 디자인 설정
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")
st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; }
    .report-box { background-color: rgba(255, 255, 255, 0.5); padding: 30px; border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.8; margin-bottom: 25px; }
    .shop-btn { display: inline-block; padding: 6px 14px; margin: 4px; background-color: white; border: 1px solid #5f0080; border-radius: 20px; font-size: 0.85em; text-decoration: none !important; color: #5f0080 !important; font-weight: bold; }
    .stButton>button { background-color: #556B2F; color: white; border-radius: 8px; width: 100%; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 메인 UI
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다."**')
st.markdown("""
<div class="report-box">
    <h4 style="color: #36454F; margin-bottom: 15px;">맛있는 요리를 발견하셨나요? <br>지금 바로 사진을 찍거나 이미지를 업로드해 보세요!</h4>
    <p style="font-size: 1.05em; color: #4F4F4F; margin-bottom: 25px;"><b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독하여 조리법을 제공해 드립니다.</p>
    <div style="font-size: 0.95em; line-height: 1.8;">
        <div style="margin-bottom: 15px;"><span style="font-size: 1.2em;">🔍</span> <b>쿠킹클론 역설계</b><br><span style="color: #666;">사진 속 재료와 조리 방식을 정밀하게 뽑아내어 누구나 쉽게 따라 할 수 있도록 설명해 드립니다.</span></div>
        <div style="margin-bottom: 15px;"><span style="font-size: 1.2em;">✨</span> <b>한 끗 차이 비법</b><br><span style="color: #666;">식당 맛을 내는 결정적 포인트와 숨겨진 비결을 제공합니다.</span></div>
        <div><span style="font-size: 1.2em;">🏠</span> <b>홈스타일 가이드</b><br><span style="color: #666;">가정에 있는 조리 도구에 최적화된 최적의 방법을 제시합니다.</span></div>
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
            with st.spinner("해독 중..."):
                res = model.generate_content(["요리 분석, 비법, 재료, 레시피 순으로 작성하고 마지막에 [Ingredients: 재료1, 재료2...] 형식을 넣으세요.", img])
                st.markdown(f'<div class="report-box">{res.text}</div>', unsafe_allow_html=True)
                if "[Ingredients:" in res.text:
                    ings = res.text.split("[Ingredients:")[1].split("]")[0].split(",")
                    st.markdown("#### 🛒 추천 신선 재료 (마켓컬리)")
                    links = "".join([f'<a href="[https://www.kurly.com/search?keyword=](https://www.kurly.com/search?keyword=){urllib.parse.quote(i.strip())}" target="_blank" class="shop-btn">💜 {i.strip()} 컬리 장보기</a>' for i in ings[:5]])
                    st.markdown(f'<div style="text-align:center;">{links}</div>', unsafe_allow_html=True)
else:
    st.warning("API_KEY를 설정해 주세요.")
