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
    API_KEY = "여기에_로컬_테스트용_키를_입력하세요"

# --- 1. 앱 디자인 (뮤트 톤 & 세련된 감성) ---
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")

st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; }
    
    .stButton>button { 
        background-color: #556B2F; color: white; border-radius: 8px; 
        width: 100%; height: 3.5em; font-weight: bold; border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #3e4e22; color: #E2D7C3; }
    
    .report-box { 
        background-color: rgba(255, 255, 255, 0.6); padding: 25px; 
        border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.8; 
        margin-bottom: 20px;
    }
    
    .sns-card {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        padding: 40px; border-radius: 25px; border: 1px solid #ddd;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        text-align: center; margin: 20px 0;
    }
    
    .shop-btn {
        display: inline-block; padding: 6px 14px; margin: 4px;
        background-color: white; border: 1px solid #556B2F;
        border-radius: 20px; font-size: 0.85em; text-decoration: none !important; 
        color: #556B2F !important; font-weight: bold;
    }
    .shop-btn:hover { background-color: #556B2F; color: white !important; }
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

# --- 3. 쇼핑 링크 생성 헬퍼 함수 ---
def make_shopping_links(ingredient_list):
    links_html = "<div style='margin-top:15px; text-align:center;'>"
    ingredients = [i.strip() for i in ingredient_list.split(',')[:5]]
    for item in ingredients:
        if len(item) > 1:
            encoded_item = urllib.parse.quote(item)
            links_html += f"<a href='https://www.coupang.com/np/search?q={encoded_item}' target='_blank' class='shop-btn'>🛒 {item} 장보기</a>"
    links_html += "</div>"
    return links_html

# --- 4. 메인 UI 및 로직 ---
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown("### **\"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다.\"**")

st.markdown("""
<div class="report-box">
    <p style="font-size: 1.05em; line-height: 1.6;">
        잊지 못할 요리를 만났을 때, 사진을 찍거나 업로드해 보세요.<br>
        <b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독하여 그 본질을 재현해 드립니다.
    </p>
    <div style="font-size: 0.9em; margin-top: 15px;">
        🔍 <b>쿠킹클론 역설계</b> | ✨ <b>한 끗 차이 비법</b> | 🏠 <b>홈스타일 가이드</b>
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

                    # --- [업그레이드: 쇼핑 및 SNS 카드] ---
                    st.divider()
                    if "[Ingredients:" in full_response:
                        try:
                            ing_part = full_response.split("[Ingredients:")[1].split("]")[0]
                            st.markdown("#### 🛒 쿠킹클론 추천 신선 재료")
                            st.markdown(make_shopping_links(ing_part), unsafe_allow_html=True)
                        except: pass

                    st.markdown("#### 📱 SNS 공유용 리포트 카드")
                    summary = full_response.split('\n')[0][:80] if full_response else "미식의 새로운 발견"
                    st.markdown(f"""
                    <div class="sns-card">
                        <h2 style="color:#556B2F; margin-bottom:5px; font-size:1.8em;">Cooking Clone</h2>
                        <p style="color:#888; font-size:0.9em; letter-spacing:2px;">CULINARY REPORT</p>
                        <div style="border-top: 1px solid #556B2F; width: 50px; margin: 20px auto;"></div>
                        <p style="font-size:1.15em; line-height:1.6; color:#444;">"{summary}..."</p>
                        <div style="margin-top:30px; font-weight:bold; color:#556B2F;">#쿠킹클론 #레시피복제 #미식라이프</div>
                    </div>
                    <p style="text-align:right; font-size:0.8em; color:#999;">위 카드를 캡처해서 SNS에 공유해 보세요!</p>
                    """, unsafe_allow_html=True)

                    st.download_button("📄 레시피 소장하기 (.txt)", data=full_response, file_name="cooking_clone_recipe.txt")
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")
else:
    st.error("⚠️ API 키 설정을 확인해 주세요.")

st.divider()
st.caption("© 2026 Cooking Clone - 쿠킹클론은 당신의 품격 있는 미식 생활을 지원합니다.")
