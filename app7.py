import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import re
import platform
import os

# -----------------------------------------------------------------------------
# 0. 한글 폰트 설정 (그래프에서 한글 깨짐 방지)
# -----------------------------------------------------------------------------
if platform.system() == 'Darwin':  # 맥(Mac)
    plt.rc('font', family='AppleGothic')
    wc_font_path = '/Library/Fonts/AppleGothic.ttf'  # 맥 워드클라우드 폰트 경로
else:  # 윈도우(Windows)
    plt.rc('font', family='Malgun Gothic')
    wc_font_path = 'C:/Windows/Fonts/malgun.ttf'  # 윈도우 맑은고딕 폰트 경로

plt.rcParams['axes.unicode_minus'] = False


# -----------------------------------------------------------------------------
# 기능 1: 데이터 불러오기 및 전처리
# -----------------------------------------------------------------------------
def load_data(file):
    try:
        # 파일 읽기
        df = pd.read_csv(file)

        # [오류 수정!] 계산해야 할 열들을 확실하게 '숫자형(float)'으로 변환합니다.
        # 문자가 섞여있다면 빈칸(NaN)으로 만들어서 오류를 방지해요.
        numeric_cols = ['통학시간', '공부시간', '스마트폰', '수면시간', '만족도']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"파일을 읽어오는 중 오류가 발생했어요. csv 파일이 맞는지 확인해주세요!\n({e})")
        return None


# -----------------------------------------------------------------------------
# 기능 2: 생활습관 차이 시각화
# -----------------------------------------------------------------------------
def plot_lifestyle(df):
    st.subheader("📊 학과별 학생들의 생활습관에는 어떤 차이가 있을까요?")

    cols = ['통학시간', '공부시간', '스마트폰', '수면시간']
    # [오류 수정!] 숫자형 데이터만 계산하도록 안전장치(numeric_only=True) 추가
    avg_data = df[cols].mean(numeric_only=True)

    fig, ax = plt.subplots(figsize=(8, 4))
    avg_data.plot(kind='bar', ax=ax, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
    ax.set_ylabel("평균 시간/분")
    plt.xticks(rotation=0)

    st.pyplot(fig)


# -----------------------------------------------------------------------------
# 기능 3: 만족도 관련성 시각화
# -----------------------------------------------------------------------------
def plot_correlation(df):
    st.subheader("📈 공부, 수면, 스마트폰 시간 등은 학교생활만족도와 어떤 관련이 있을까요?")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    cols = ['공부시간', '수면시간', '스마트폰']
    colors = ['blue', 'green', 'red']

    for i, col in enumerate(cols):
        # 결측치(빈 데이터)가 있으면 산점도 그래프에서 오류가 날 수 있어 제거합니다.
        temp_df = df.dropna(subset=[col, '만족도'])
        axes[i].scatter(temp_df[col], temp_df['만족도'], color=colors[i], alpha=0.6)
        axes[i].set_xlabel(col)
        axes[i].set_ylabel('만족도')
        axes[i].set_title(f"{col} vs 만족도")

    st.pyplot(fig)


# -----------------------------------------------------------------------------
# 기능 4: 한 줄 의견 분석 (빈도, 긍정/부정, 워드클라우드)
# -----------------------------------------------------------------------------
def analyze_comments(df):
    st.subheader("💬 학생들이 작성한 한 줄 의견에는 어떤 단어가 많이 등장할까요?")

    if '한줄의견' not in df.columns:
        st.warning("데이터에 '한줄의견' 열이 없습니다.")
        return

    text_data = " ".join(df['한줄의견'].dropna().astype(str))
    clean_text = re.sub(r'[^\w\s]', '', text_data)
    words = [w for w in clean_text.split() if len(w) > 1]

    if not words:
        st.info("분석할 텍스트 데이터가 부족합니다.")
        return

    # 1. 자주 등장하는 단어 상위 10개 막대그래프
    word_counts = Counter(words)
    top_10 = word_counts.most_common(10)

    # [오류 수정!] 딕셔너리의 키와 값을 리스트로 확실하게 변환해서 그래프 오류 방지
    words_list = [item[0] for item in top_10]
    counts_list = [item[1] for item in top_10]

    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(words_list, counts_list, color='mediumpurple')
    ax1.set_title("자주 등장하는 상위 10개 단어")
    st.pyplot(fig1)

    # 2. 워드클라우드 생성
    st.write("**[☁️ 한 줄 의견 워드클라우드]**")
    try:
        # [오류 수정!] 정확한 파일 경로(wc_font_path)를 지정하여 생성
        wc = WordCloud(font_path=wc_font_path, background_color='white', width=800, height=400)
        cloud = wc.generate_from_frequencies(word_counts)

        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.imshow(cloud, interpolation='bilinear')
        ax2.axis('off')
        st.pyplot(fig2)
    except Exception as e:
        st.warning(f"폰트 문제로 워드클라우드를 만들 수 없어요. (에러: {e})")

    # 3. 긍정/부정 단어 분석
    st.write("**[👍/👎 긍정 및 부정 단어 등장 횟수]**")
    pos_keywords = ['좋아', '재미', '맛있', '예뻐', '도움', '만족', '최고']
    neg_keywords = ['부족', '피곤', '불편', '힘들', '어려', '길어', '별로']

    pos_count = sum(1 for w in words if any(pos in w for pos in pos_keywords))
    neg_count = sum(1 for w in words if any(neg in w for neg in neg_keywords))

    col1, col2 = st.columns(2)
    col1.metric("😊 긍정적인 단어 등장 횟수", f"{pos_count}회")
    col2.metric("😥 부정적인 단어 등장 횟수", f"{neg_count}회")


# -----------------------------------------------------------------------------
# 메인 실행부
# -----------------------------------------------------------------------------
def main():
    st.title("🎓 캠퍼스 생활 설문조사 웹앱")