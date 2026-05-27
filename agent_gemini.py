import os
import streamlit as st
import matplotlib.pyplot as plt
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ==========================================
# 🔥 [여기에 추가] Matplotlib 한글 폰트 깨짐 방지 설정
# ==========================================
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우 기본 맑은고딕 설정
matplotlib.rcParams['axes.unicode_minus'] = False    # 마이너스 기호 깨짐 방지
# ==========================================

# 1. 환경 변수 로드 및 Gemini 클라이언트 초기화
load_dotenv()
client = genai.Client()

# 2. AI의 역할 지시문 (페르소나 설정)
SYSTEM_PROMPT = """
당신은 대학생들을 지도하는 전문 헬스 트레이너이자 영양사인 'AI 피트니스 코치'입니다.
사용자가 입력한 [키, 몸무게, 운동 목적]을 바탕으로 아주 구체적이고 현실적인 '주간 운동 루틴'과 '식단 가이드'를 짜주어야 합니다.

답변할 때 다음 규칙을 반드시 지키세요:
1. 핵심 요약을 맨 처음에 깔끔하게 제공하세요.
2. 운동 루틴은 요일별(월~일)로 나누어 작성하고, 세트 수와 횟수를 명시하세요.
3. ★★중요★★ 운동 기구나 운동법을 언급할 때는, 사용자가 기구 사용법을 영상으로 바로 찾아볼 수 있도록 마크다운 형식의 유튜브 검색 링크를 반드시 첨부하세요.
   - 링크 형식 예시: [📺 기구 사용법 보기](https://www.youtube.com/results?search_query=체스트+프레스+사용법)
4. 식단은 아침, 점심, 저녁, 간식으로 나누어 대학생이 학식이나 자취방에서 챙겨 먹기 쉬운 현실적인 메뉴로 추천하세요.
5. 말투는 친절하고 파이팅 넘치는 톤앤매너를 유지하고, 답변은 한국어로 작성하세요.
"""

# 3. Streamlit 웹 UI 설정
st.set_page_config(page_title="AI 맞춤형 운동 루틴 생성기", page_icon="🏋️‍♂️")
st.title("🏋️‍♂️ 대학생 맞춤형 AI 운동/식단 코치")
st.caption("Google Gemini 2.5 기반 | 유튜브 연동 피트니스 대시보드")

# 사이드바: 사용자 신체 정보 및 목적 입력 창 구성
with st.sidebar:
    st.header("📋 나의 신체 정보 입력")
    
    # 키와 몸무게 입력 (슬라이더)
    height = st.slider("현재 키 (cm)", 140, 210, 173)
    weight = st.slider("현재 몸무게 (kg)", 40, 130, 68)
    
    # 운동 목적 선택 박스
    purpose = st.selectbox(
        "운동 목적을 선택하세요",
        ["다이어트 (체지방 감량)", "유지어트 (현재 체중 유지)", "근비대 (근육량 증가 및 벌크업)"]
    )
    
    st.markdown("---")
    # 분석 시작 버튼
    submit_button = st.button("💪 맞춤 루틴/식단 생성하기")

# 4. 세션 상태(Session State)를 활용해 결과 유지하기
if "fitness_result" not in st.session_state:
    st.session_state.fitness_result = None
if "chart_data" not in st.session_state:
    st.session_state.chart_data = None

# 5. 버튼을 눌렀을 때 실행되는 로직
if submit_button:
    # AI에게 보낼 맞춤형 질문 조립
    user_message = f"내 키는 {height}cm이고 몸무게는 {weight}kg이야. 내 목적은 {purpose}야. 맞춤 운동 루틴과 식단을 짜줘!"
    
    # 구글 가이드라인에 따른 대화 포맷 생성
    contents_history = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)]
        )
    ]
    
    # 에러가 났던 공백과 들여쓰기를 완벽하게 정정했습니다.
    with st.spinner("AI 코치가 당신의 맞춤형 루틴과 유튜브 가이드를 준비하고 있습니다..."):
        try:
            # Gemini API 호출
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_history,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                ),
            )
            # 결과를 세션 상태에 저장
            st.session_state.fitness_result = response.text
            
            # 운동 목적에 따라 시각화할 차트 데이터 분기 설정
            if "다이어트" in purpose:
                st.session_state.chart_data = {"유산소": 50, "하체": 20, "상체": 20, "코어": 10}
            elif "유지어트" in purpose:
                st.session_state.chart_data = {"유산소": 30, "하체": 30, "상체": 30, "코어": 10}
            else:
                st.session_state.chart_data = {"유산소": 10, "하체": 40, "상체": 40, "코어": 10}
                
        except Exception as e:
            st.error(f"⚠️ 에러가 발생했습니다: {e}")

# 6. 결과 화면 출력 영역
if st.session_state.fitness_result:
    # 화면을 두 개의 열로 분할하여 배치
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📋 AI 코치의 맞춤 제안서")
        st.markdown(st.session_state.fitness_result)
        
    with col2:
        st.subheader("📊 추천 운동 부위별 비중")
        # Matplotlib을 이용한 파이 차트 시각화 구현
        data = st.session_state.chart_data
        fig, ax = plt.subplots(figsize=(5, 5))
        
        ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=90, 
               colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
        ax.axis('equal')  
        
        st.pyplot(fig)