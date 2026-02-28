import streamlit as st
import google.generativeai as genai
from PIL import Image
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
    .intro-box { background-color: rgba(255, 255, 255, 0.5); padding: 20px 25px; border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.5; margin-top: 10px; margin-bottom: 15px; }
    .shop-btn { display: inline-block; padding: 6px 14px; margin: 4px; background-color: white; border: 1px solid #5f0080; border-radius: 20px; font-size: 0.85em; text-decoration: none !important; color: #5f0080 !important; font-weight: bold; }
    .shop-btn:hover { background-color: #5f0080; color: white !important; }
    .stButton>button { background-color: #556B2F; color: white; border-radius: 8px; width: 100%; height: 3.5em; font-weight: bold; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 메인 UI
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다."**')

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

# 자동 엔진 탐색기
@st.cache_resource
def initialize_engine(api_key):
    if not api_key: return None
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision']:
            for m in models:
                if target in m: return genai.GenerativeModel(m)
        return genai.GenerativeModel(models[0]) if models else None
    except:
        return None

# 4. 분석 로직
if API_KEY:
    model = initialize_engine(API_KEY)
    
    # 탭 구성 (직접 촬영 / 이미지 업로드)
    tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
    source = None
    
    with tab1:
        st.caption("💡 스마트폰에서 촬영이 안 될 경우, 브라우저 설정에서 '카메라 접근 권한'을 허용해 주세요.")
        cam_source = st.camera_input("요리 사진을 촬영하세요")
    with tab2:
        file_source = st.file_uploader("사진을 선택하세요", type=["jpg", "png", "jpeg"])
    
    # 사용자가 선택한 소스 확인
    if cam_source:
        source = cam_source
    elif file_source:
        source = file_source
        
    if source:
        img = Image.open(source)
        st.image(img, use_container_width=True)
        
        if st.button("✨ 비법 복제하기"):
            if model is None:
                st.error("AI 엔진을 불러오지 못했습니다. API 키를 다시 확인해 주세요.")
            else:
                report_placeholder = st.empty() # 스트리밍을 위한 빈 공간 생성
                full_text = ""
                
                # 프롬프트: 시적이고 간결하게 지시
                prompt = """
                당신은 시적이고 세련된 미식 평론가이자 요리 연구가 '쿠킹클론'입니다.
                마크다운 코드 기호(```)는 절대 쓰지 마세요.
                다음 4단계를 아주 간결하고 느낌 있게 작성하세요.
                
                1. 쿠킹클론 요리 분석: 구구절절한 설명은 빼고, 요리의 시각적 매력과 맛의 본질을 시적인 평론가 톤으로 3~4문장으로 짧고 강렬하게 표현하세요.
                2. 한 끗 차이 비법: 핵심 비결만 2~3문장으로 임팩트 있게.
                3. 역설계 재료: 보기 쉽게 간단한 목록으로.
                4. 홈스타일 레시피: 집에서 따라하기 쉽게 요약된 과정으로.
                
                마지막에 반드시 [Ingredients: 재료1, 재료2, 재료3, 재료4, 재료5] 형식을 포함하세요.
                """
                try:
                    # 실시간 스트리밍 부활
                    response = model.generate_content([prompt, img], stream=True)
                    for chunk in response:
                        full_text += chunk.text
                        # 혹시 모를 기호 텍스트 세탁
                        clean_text = full_text.replace("```markdown", "").replace("```html", "").replace("```", "")
                        report_placeholder.markdown(f"**미식 데이터를 해독 중입니다...**\n\n---\n{clean_text}")
                    
                    # 완료 후 선을 그어 깔끔하게 마무리
                    report_placeholder.markdown(f"---\n{clean_text}\n---")
                    
                    # 마켓컬리 쇼핑 버튼 링크 생성
                    if "[Ingredients:" in clean_text:
                        ings = clean_text.split("[Ingredients:")[1].split("]")[0].split(",")
                        st.markdown("#### 🛒 추천 신선 재료 (마켓컬리)")
                        links = "".join([f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(i.strip())}" target="_blank" class="shop-btn">💜 {i.strip()} 컬리 장보기</a>' for i in ings[:5]])
                        st.markdown(f'<div style="text-align:center;">{links}</div>', unsafe_allow_html=True)
                        
                    # PDF용 HTML 리포트 소스 생성
                    display_text = clean_text.split('[Ingredients:')[0].strip() # 재료 태그는 빼고 출력
                    html_report = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Cooking Clone Report</title>
                        <style>
                            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 40px; color: #333; background-color: #f9f9f9; line-height: 1.6; }}
                            h1 {{ color: #556B2F; border-bottom: 2px solid #556B2F; padding-bottom: 10px; }}
                            pre {{ font-family: inherit; white-space: pre-wrap; word-wrap: break-word; font-size: 15px; background: #fff; padding: 25px; border-radius: 10px; border: 1px solid #ddd; }}
                        </style>
                    </head>
                    <body>
                        <h1>🍳 Cooking Clone Recipe Report</h1>
                        <p style="color:#666; font-style:italic;">"당신의 주방에서 영원한 레시피가 됩니다."</p>
                        <pre>{display_text}</pre>
                    </body>
                    </html>
                    """
                    
                    # 리포트 다운로드 버튼
                    st.divider()
                    st.download_button(
                        label="📄 리포트 저장하기 (웹/PDF용)", 
                        data=html_report, 
                        file_name="cooking_clone_report.html", 
                        mime="text/html"
                    )
                    st.caption("💡 팁: 다운로드한 파일을 스마트폰 브라우저나 크롬에서 여신 후, **[인쇄 -> PDF로 저장]**을 누르시면 깔끔한 PDF로 평생 소장하실 수 있습니다.")
                    
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")
else:
    st.warning("Secrets 설정에서 API_KEY를 입력해 주세요.")
