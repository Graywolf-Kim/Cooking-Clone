import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import urllib.parse

# ==========================================
# 🔑 보안 설정: Streamlit Cloud Secrets 사용
# ==========================================
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "여기에_키를_넣으세요" # 로컬 테스트용

# --- 1. 앱 디자인 (뮤트 톤 & 세련된 감성) ---
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")

st.markdown("""
    <style>
    /* 전체 배경 및 폰트 설정 */
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; }
    
    /* 버튼 스타일 */
    .stButton>button { 
        background-color: #556B2F; color: white; border-radius: 8px; 
        width: 100%; height: 3.5em; font-weight: bold; border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #3e4e22; color: #E2D7C3; }
    
    /* 리포트 박스 스타일 */
    .report-box { 
        background-color: rgba(255, 255, 255, 0.5); padding: 30px; 
        border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.8; 
        margin-bottom: 25px;
    }
    
    /* 쇼핑 버튼 스타일 (마켓컬리 브랜드 컬러 느낌 반영) */
    .shop-btn {
        display: inline-block; padding: 6px 14px; margin: 4px;
        background-color: white; border: 1px solid #5f0080;
        border-radius: 20px; font-size: 0.85em; text-decoration: none !important; 
        color: #5f0080 !important; font-weight: bold;
    }
    .shop-btn:hover { background-color: #5f0080; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 쿠킹클론 엔진 자동 탐색 ---
@st.cache_resource
def initialize_engine(api_key):
    if not api_key or "여기에" in api_key: return None
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['gemini-3-flash', 'gemini-1.5-flash', 'flash']:
            for m_name in available_models:
                if target in m_name: return genai.GenerativeModel(m_name)
        return genai.GenerativeModel(available_models[0])
    except: return None

model = initialize_engine(API_KEY)

# --- 3. 쇼핑 링크 생성 헬퍼 함수 (마켓컬리 연결) ---
def make_shopping_links(ingredient_list):
    links_html = "<div style='margin-top:15px; text-align:center;'>"
    ingredients = [i.strip() for i in ingredient_list.split(',')[:5]]
    for item in ingredients:
        if len(item) > 1:
            # 마켓컬리 검색 URL 구조 적용
            encoded_item = urllib.parse.quote(item)
            links_html += f"<a href='https://www.kurly.com/search?keyword={encoded_item}' target='_blank' class='shop-btn'>💜 {item} 컬리 장보기</a>"
    links_html += "</div>"
    return links_html

# --- 4. 메인 UI 및 로직 ---
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown("### **\"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다.\"**")

# 사용자 요청 문구 반영
st.markdown("""
<div class="report-box">
    <h4 style="color: #36454F; margin-bottom: 15px;">맛있는 요리를 발견하셨나요? <br>지금 바로 사진을 찍거나 이미지를 업로드해 보세요!</h4>
    <p style="font-size: 1.05em; color: #4F4F4F; margin-bottom: 25px;">
        <b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독하여 조리법을 제공해 드립니다.
    </p>
    
    <div style="font-size: 0.95em; line-height: 1.8;">
        <div style="margin-bottom: 15px;">
            <span style="font-size: 1.2em;">🔍</span> <b>쿠킹클론 역설계</b><br>
            <span style="color: #666;">사진 속 재료와 조리 방식을 정밀하게 뽑아내어 누구나 쉽게 따라 할 수 있도록 설명해 드립니다.</span>
        </div>
        <div style="margin-bottom: 15px;">
            <span style="font-size: 1.2em;">✨</span> <b>한 끗 차이 비법</b><br>
            <span style="color: #666;">식당 맛을 내는 결정적 포인트와 숨겨진 비결을 제공합니다.</span>
        </div>
        <div>
            <span style="font-size: 1.2em;">🏠</span> <b>홈스타일 가이드</b><br>
            <span style="color: #666;">가정에 있는 조리 도구에 최적화된 최적의 방법을 제시합니다.</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if model:
    tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
    source = None
    with tab1: source = st.camera_input("오늘의 미식을 기록하세요")
    with tab2:
        if not source: source = st.file_uploader("분석할 요리 사진 선택", type=["jpg", "png", "jpeg"])

    if source:
        img = Image.open(source)
        st.image(img, caption="입력된 미식 데이터", use_container_width=True)
        
        if st.button("✨ 쿠킹클론으로 비법 복제하기"):
            report_placeholder = st.empty()
            full_response = ""

            with st.spinner("쿠킹클론이 맛의 본질을 해독하고 있습니다..."):
                prompt = """
                당신은 전문 미식 가이드 '쿠킹클론'입니다. 
                1. 쿠킹클론 요리 분석 / 2. 한 끗 차이 비법 / 3. 역설계 재료 / 4. 홈스타일 클론 레시피 순서로 작성하세요.
                *중요: 답변 맨 마지막에 반드시 [Ingredients: 재료1, 재료2, 재료3, 재료4, 재료5] 형식으로 핵심 재료 5개를 포함하세요.*
                *결과물에 'AI' 단어를 사용하지 말고, 품격 있고 다정한 어조를 유지하세요.*
                """
                try:
                    response = model.generate_content([prompt, img], stream=True)
                    for chunk in response:
                        full_response += chunk.text
                        report_placeholder.markdown(f'<div class="report-box">{full_response}</div>', unsafe_allow_html=True)
                    
                    st.success("미식 해독이 완료되었습니다.")

                    # --- [업그레이드: 마켓컬리 쇼핑 기능] ---
                    st.divider()
                    if "[Ingredients:" in full_response:
                        try:
                            ing_part = full_response.split("[Ingredients:")[1].split("]")[0]
                            st.markdown("#### 🛒 쿠킹클론 추천 신선 재료 (마켓컬리)")
                            st.markdown(make_shopping_links(ing_part), unsafe_allow_html=True)
                        except: pass

                    # 텍스트 파일 저장 버튼
                    st.download_button("📄 레시피 소장하기 (.txt)", data=full_response, file_name="cooking_clone_recipe.txt")
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")
else:
    st.error("⚠️ API 키 설정을 확인해 주세요.")

st.divider()
st.caption("© 2026 Cooking Clone - 쿠킹클론은 당신의 품격 있는 미식 생활을 지원합니다.")
