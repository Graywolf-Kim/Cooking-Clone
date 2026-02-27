import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# ==========================================
# 🔑 여기에 발급받으신 API 키를 입력하세요
# ==========================================
API_KEY = st.secrets["API_KEY"]
# ==========================================

# --- 1. 앱 설정 및 세련된 뮤트 톤 디자인 ---
st.set_page_config(page_title="Cooking Clone", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; }
    .stButton>button { 
        background-color: #556B2F; color: white; border-radius: 8px; 
        width: 100%; height: 3.5em; font-weight: bold; border: none;
    }
    .report-box { 
        background-color: rgba(255, 255, 255, 0.5); padding: 25px; 
        border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.8; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 쿠킹클론 엔진 자동 탐색 로직 (404 에러 원천 봉쇄) ---
@st.cache_resource
def initialize_engine(api_key):
    if not api_key or api_key == "여기에_발급받은_키를_입력하세요": return None
    try:
        genai.configure(api_key=api_key)
        # 현재 API 키로 사용 가능한 모든 모델 목록 호출
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 속도가 빠른 'flash' 모델 우선 검색 후 연결
        for target in ['gemini-1.5-flash', 'gemini-1.5-pro', 'flash']:
            for m_name in available_models:
                if target in m_name:
                    return genai.GenerativeModel(m_name)
        return genai.GenerativeModel(available_models[0]) # 찾지 못할 경우 첫 번째 모델 강제 연결
    except Exception as e:
        st.error(f"엔진 초기화 실패: {e}")
        return None

model = initialize_engine(API_KEY)

# --- 3. 메인 화면: 세련된 설명란 복구 ---
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown("### **\"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다.\"**")

st.markdown("""
<div class="report-box">
    <p style="font-size: 1.05em; line-height: 1.6;">
        잊지 못할 요리를 만났을 때, 지금 바로 사진을 찍거나 이미지를 업로드해 보세요.<br>
        <b>쿠킹클론</b>이 시각적 데이터를 정밀하게 해독하여, 누구나 품격 있는 맛을 재현할 수 있도록 안내합니다.
    </p>
    <div style="margin-top: 20px;">
        <div style="margin-bottom: 12px;">
            <b>🔍 쿠킹클론 역설계</b>: 사진 한 장에 담긴 식재료의 조화와 조리 원리를 정밀하게 분석하여 맛의 구조를 완벽히 이해하도록 돕습니다.
        </div>
        <div style="margin-bottom: 12px;">
            <b>✨ 한 끗 차이 비법</b>: 평범함과 비범함을 가르는 미묘한 차이, 그 '결정적 변곡점'을 포착하여 식당의 깊은 풍미를 완성하는 비책을 전수합니다.
        </div>
        <div>
            <b>🏠 홈스타일 가이드</b>: 당신의 주방에 있는 일상의 도구들에 최적화된, 가장 효율적이고 현실적인 조리 경로를 설계해 드립니다.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 4. 사용자 입력 및 분석 로직 ---
if model:
    tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
    source = None
    with tab1: source = st.camera_input("오늘의 미식을 기록하세요")
    with tab2:
        if not source: source = st.file_uploader("분석할 요리 사진 선택", type=["jpg", "png", "jpeg"])

    if source is not None:
        img = Image.open(source)
        st.image(img, caption="입력된 미식 데이터", use_container_width=True)
        
        if st.button("✨ 쿠킹클론으로 비법 복제하기"):
            report_placeholder = st.empty()
            full_response = ""

            with st.spinner("쿠킹클론이 맛의 본질을 해독하고 있습니다..."):
                prompt = """
                당신은 전문 미식 가이드 '쿠킹클론'입니다. 사진을 분석하여 다음 내용을 작성하세요.
                1. 쿠킹클론 요리 분석 / 2. 한 끗 차이 비법 / 3. 역설계 재료 / 4. 홈스타일 클론 레시피
                모든 과정에서 'AI'라는 단어를 사용하지 말고 '쿠킹클론'이라 칭하세요. 
                품격 있고 다정한 어조로 스트리밍 답변을 제공하세요.
                """
                try:
                    # 스트리밍 분석 (속도와 지루함 해소)
                    response = model.generate_content([prompt, img], stream=True)
                    for chunk in response:
                        full_response += chunk.text
                        report_placeholder.markdown(f'<div class="report-box">{full_response}</div>', unsafe_allow_html=True)
                    
                    st.success("분석이 완료되었습니다!")

                    # --- 공유 및 저장 섹션 ---
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("💡 **카톡 공유 팁**: 아래 내용을 드래그하여 복사 후 붙여넣으세요.")
                        st.text_area("결과 요약 (복사용)", value=full_response, height=150)
                    with col2:
                        st.download_button(
                            label="📄 레시피 파일(.txt) 저장",
                            data=full_response,
                            file_name="cooking_clone_recipe.txt",
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다. (상세: {e})")
else:
    st.error("⚠️ 쿠킹클론 엔진을 초기화할 수 없습니다. API 키를 확인해 주세요.")

st.divider()
st.caption("© 2026 Cooking Clone - 쿠킹클론은 당신의 품격 있는 미식 생활을 지원합니다.")