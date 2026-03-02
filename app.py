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

# 2. 디자인 설정
st.set_page_config(page_title="Cooking Clone", layout="centered", page_icon="🍳")
st.markdown("""
    <style>
    .stApp { background-color: #DBCFBB; color: #36454F; }
    h1, h2, h3 { color: #556B2F !important; font-family: 'Nanum Gothic', sans-serif; margin-bottom: 5px; }
    .intro-box { background-color: rgba(255, 255, 255, 0.5); padding: 20px 25px; border-radius: 15px; border-left: 8px solid #556B2F; line-height: 1.5; margin-top: 10px; margin-bottom: 15px; }
    .shop-btn { display: inline-block; padding: 2px 10px; margin-left: 10px; background-color: white; border: 1px solid #5f0080; border-radius: 15px; font-size: 0.8em; text-decoration: none !important; color: #5f0080 !important; font-weight: bold; vertical-align: middle; }
    .shop-btn:hover { background-color: #5f0080; color: white !important; }
    /* 링크가 포함된 리스트 아이템 정렬을 위해 */
    li { margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 메인 UI
st.title("🍳 쿠킹클론 (Cooking Clone)")
st.markdown('### **"찰나의 미식, 당신의 주방에서 영원한 레시피가 됩니다."**')

st.markdown("""
<div class="intro-box">
    <p style="font-size: 1.0em; color: #4F4F4F; margin-bottom: 10px;">사진을 업로드하면 <b>쿠킹클론</b>이 미식 데이터를 정밀하게 해독합니다.</p>
    <div style="font-size: 0.95em;">
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">🔍</span> <b>역설계:</b> 재료와 조리 방식을 정밀하게 뽑아내어 쉽게 설명합니다.</div>
        <div style="margin-bottom: 8px;"><span style="font-size: 1.1em;">✨</span> <b>비법:</b> 식당 맛을 내는 결정적 포인트와 비결을 제공합니다.</div>
        <div><span style="font-size: 1.1em;">🏠</span> <b>가이드:</b> 가정에 있는 조리 도구에 최적화된 방법을 제시합니다.</div>
    </div>
</div>
""", unsafe_allow_html=True)

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
    
    tab1, tab2 = st.tabs(["📸 직접 촬영", "📁 이미지 업로드"])
    source = None
    
    with tab1:
        st.caption("💡 참고: 브라우저 환경상 카메라 배율(Zoom)은 기기 기본값을 따릅니다.")
        cam_source = st.camera_input("요리 사진을 촬영하세요")
    with tab2:
        file_source = st.file_uploader("사진을 선택하세요", type=["jpg", "png", "jpeg"])
    
    if cam_source:
        source = cam_source
    elif file_source:
        source = file_source
        
    # 이미지가 업로드되면 버튼 없이 즉시 실행
    if source:
        img = Image.open(source)
        st.image(img, use_container_width=True)
        
        if model is None:
            st.error("AI 엔진을 불러오지 못했습니다. API 키를 다시 확인해 주세요.")
        else:
            # 상태 표시 스피너 추가 (비법 복제 중 표기 및 움직임)
            with st.spinner("✨ 비법 복제 중... 미식 데이터를 정밀 해독하고 있습니다."):
                report_placeholder = st.empty() 
                full_text = ""
                
                # 프롬프트 수정: 내용 간략화, 2/4인분 명확화, 정량화, 링크 치환용 태그 추가
                prompt = """
                당신은 시적이고 세련된 미식 평론가이자 요리 연구가 '쿠킹클론'입니다.
                결과물을 출력할 때 반드시 아래의 4가지 제목을 똑같이 사용해서 작성하세요. 
                제목은 반드시 마크다운의 '###' 기호를 써서 크고 굵게 만들어야 합니다.
                
                ### 요리분석 :
                (구구절절한 설명 없이, 요리의 시각적 매력과 맛의 본질을 1~2문장으로 짧고 매우 강렬하게 평론할 것)
                
                ### 한끗차이 :
                (식당 맛을 내는 핵심 비결을 단 1문장으로 임팩트 있게 작성할 것)
                
                ### 역설계 재료 (2인분 기준) :
                (각 재료의 양을 1T, 2tsp, 100g 등으로 명확히 정량화하여 목록으로 작성할 것. 
                중요: 각 재료 항목의 맨 끝에는 반드시 '%KURLY_LINK_핵심재료명%' 이라는 태그를 붙이세요. 
                예시: - 돼지고기 삼겹살 200g %KURLY_LINK_삼겹살%)
                
                ### 홈스타일 레시피 :
                (집에서 따라하기 쉽게 요약된 과정으로 번호 매겨서 작성)
                
                * 마크다운 코드 블록 기호(```)는 절대 쓰지 마세요.
                """
                try:
                    response = model.generate_content([prompt, img], stream=True)
                    for chunk in response:
                        full_text += chunk.text
                        clean_text = full_text.replace("```markdown", "").replace("```html", "").replace("```", "")
                        
                        # %KURLY_LINK_재료명% 태그를 실제 HTML 버튼 링크로 정규식 치환
                        display_text = re.sub(
                            r'%KURLY_LINK_(.*?)%', 
                            lambda m: f'<a href="https://www.kurly.com/search?keyword={urllib.parse.quote(m.group(1).strip())}" target="_blank" class="shop-btn">💜 {m.group(1).strip()} 컬리 장보기</a>', 
                            clean_text
                        )
                        
                        report_placeholder.markdown(f"---\n{display_text}")
                    
                    # 최종 출력
                    report_placeholder.markdown(f"---\n{display_text}\n---", unsafe_allow_html=True)
                    
                    # PDF용 HTML 리포트 소스 생성 (버튼 디자인 등 포함)
                    html_report = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Cooking Clone Report</title>
                        <style>
                            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 40px; color: #333; background-color: #f9f9f9; line-height: 1.6; }}
                            h1 {{ color: #556B2F; border-bottom: 2px solid #556B2F; padding-bottom: 10px; }}
                            h3 {{ color: #556B2F; margin-top: 20px; }}
                            .shop-btn {{ display: none; }} /* 인쇄용 PDF에서는 장보기 버튼 숨김 */
                            .content-box {{ background: #fff; padding: 25px; border-radius: 10px; border: 1px solid #ddd; }}
                        </style>
                    </head>
                    <body>
                        <h1>🍳 Cooking Clone Recipe Report</h1>
                        <p style="color:#666; font-style:italic;">"당신의 주방에서 영원한 레시피가 됩니다."</p>
                        <div class="content-box">
                            {display_text.replace(r'\n', '<br>')}
                        </div>
                    </body>
                    </html>
                    """
                    
                    st.divider()
                    st.download_button(
                        label="📄 리포트 저장하기 (웹/PDF용)", 
                        data=html_report, 
                        file_name="cooking_clone_report.html", 
                        mime="text/html"
                    )
                    st.caption("💡 팁: 다운로드한 파일을 크롬 등에서 여신 후, **[인쇄 -> PDF로 저장]**을 누르시면 평생 소장하실 수 있습니다.")
                    
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")
else:
    st.warning("Secrets 설정에서 API_KEY를 입력해 주세요.")
