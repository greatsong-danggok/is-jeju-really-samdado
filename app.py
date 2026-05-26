"""
탐구 보고서 대시보드: 제주도가 '삼다도'라는 말은 진짜인가?
- 데이터: 행정안전부 주민등록 연령별 인구현황 (2026년 4월)
- 분석 대상: '여자가 많다'는 통념을 인구 데이터로 검증
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="삼다도 가설 검증 | 탐구 보고서",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 사용자 정의 스타일 (제주 현무암 + 유채꽃 톤)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Gowun+Dodum&display=swap');

    html, body, [class*="css"] {
        font-family: 'Gowun Dodum', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Nanum Myeongjo', serif;
        letter-spacing: -0.02em;
    }
    /* 보고서 제목 */
    .report-title {
        font-family: 'Nanum Myeongjo', serif;
        font-weight: 800;
        font-size: 2.6rem;
        line-height: 1.2;
        color: #1f2933;
        border-bottom: 4px solid #2d3e2d;
        padding-bottom: 0.6rem;
        margin-bottom: 0.4rem;
    }
    .report-subtitle {
        font-size: 1.05rem;
        color: #5b6770;
        margin-bottom: 1.4rem;
    }
    /* 가설 / 결론 박스 */
    .hypothesis-box {
        background: linear-gradient(135deg, #f7f3e8 0%, #f0e9d2 100%);
        border-left: 6px solid #b8862f;
        padding: 1.1rem 1.3rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .finding-box {
        background: #f4f1ec;
        border: 1px solid #d6cfc2;
        border-radius: 6px;
        padding: 1.1rem 1.3rem;
        margin: 1rem 0;
    }
    .finding-label {
        display: inline-block;
        background: #2d3e2d;
        color: #f5f0e3;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        padding: 0.2rem 0.7rem;
        border-radius: 2px;
        margin-bottom: 0.6rem;
    }
    /* 강조 숫자 */
    .stMetric {
        background: #fafaf7;
        border: 1px solid #e8e4d8;
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
    }
    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3e2d 0%, #1f2b1f 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #f5f0e3 !important;
    }
    /* 인용 캡션 */
    .data-caption {
        font-size: 0.82rem;
        color: #8b8578;
        font-style: italic;
        margin-top: -0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# 데이터 로드 및 가공
# ─────────────────────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "data" / "202604_연령별인구현황_월간.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, encoding="cp949", thousands=",")
    # 행정구역 분리
    df["code"] = df["행정구역"].apply(
        lambda s: re.search(r"\((\d+)\)", s).group(1) if re.search(r"\((\d+)\)", s) else None
    )
    df["name"] = df["행정구역"].apply(lambda s: re.sub(r"\s*\(\d+\)\s*$", "", s).strip())

    def level(code: str) -> str:
        if code.endswith("00000000"):
            return "시도"
        if code.endswith("000000"):
            return "시군구"
        return "읍면동"

    df["level"] = df["code"].apply(level)
    return df


df = load_data()

PREFIX = "2026년04월"
MALE_TOTAL = f"{PREFIX}_남_총인구수"
FEMALE_TOTAL = f"{PREFIX}_여_총인구수"


def age_cols(sex: str, ages: range) -> list[str]:
    return [f"{PREFIX}_{sex}_{i}세" for i in ages]


# 시도 단위 집계
sido = df[df["level"] == "시도"].copy()
sido["남"] = sido[MALE_TOTAL]
sido["여"] = sido[FEMALE_TOTAL]
sido["총인구"] = sido["남"] + sido["여"]
sido["여성비율"] = sido["여"] / sido["총인구"] * 100
sido["성비"] = sido["남"] / sido["여"] * 100  # 여자 100명당 남자 수

# 제주 시군구
jeju_sigungu = df[(df["level"] == "시군구") & (df["name"].str.startswith("제주특별자치도"))].copy()
jeju_sigungu["남"] = jeju_sigungu[MALE_TOTAL]
jeju_sigungu["여"] = jeju_sigungu[FEMALE_TOTAL]
jeju_sigungu["총인구"] = jeju_sigungu["남"] + jeju_sigungu["여"]
jeju_sigungu["여성비율"] = jeju_sigungu["여"] / jeju_sigungu["총인구"] * 100
jeju_sigungu["short_name"] = jeju_sigungu["name"].str.replace("제주특별자치도 ", "", regex=False)

# 색상 팔레트 (제주 풍경에서 차용)
COLOR_MALE = "#5b7a8a"       # 제주 바다
COLOR_FEMALE = "#c97b63"     # 유채꽃 보색
COLOR_JEJU = "#2d3e2d"       # 한라산 숲
COLOR_OTHER = "#c9c2b0"      # 현무암 회색
COLOR_ACCENT = "#b8862f"     # 황금

# ─────────────────────────────────────────────────────────────────────────────
# 사이드바: 보고서 목차
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📑 탐구 보고서 목차")
    section = st.radio(
        "섹션 선택",
        [
            "표지 · 연구 동기",
            "1. 가설 설정",
            "2. 검증① 시도별 여성 비율",
            "3. 검증② 연령대별 성비",
            "4. 검증③ 제주 내부 들여다보기",
            "5. 가설 재해석",
            "6. 결론 및 제언",
            "📊 원자료 살펴보기",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        """
        **데이터 출처**
        행정안전부 주민등록 인구통계
        2026년 4월 기준

        **분석 단위**
        17개 시도 + 제주 시군구 2곳

        **사용 도구**
        Python · Streamlit · Plotly
        """
    )

# ─────────────────────────────────────────────────────────────────────────────
# 섹션 라우팅
# ─────────────────────────────────────────────────────────────────────────────

# ════════════════════════════════════════════════════════════════════════════
# 표지
# ════════════════════════════════════════════════════════════════════════════
if section == "표지 · 연구 동기":
    st.markdown('<div class="report-title">제주도는 정말 ‘삼다도(三多島)’인가?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="report-subtitle">주민등록 인구 데이터로 검증하는 오래된 통념 — 2026년 4월 기준</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.markdown(
            """
            ### 🌋 연구 동기

            제주도는 예로부터 **‘삼다도(三多島)’**, 즉 **돌·바람·여자가 많은 섬**이라고 불려왔다.
            돌과 바람은 화산섬이라는 지형 특성에서 쉽게 납득이 간다.
            그렇다면 **‘여자가 많다’는 말도 오늘날까지 사실일까?**

            이 의문에서 출발해, 가장 최근의 공식 인구 통계인
            **행정안전부 주민등록 연령별 인구현황(2026년 4월)** 을 분석해
            ‘삼다도’ 통념의 마지막 한 축을 데이터로 검증해본다.

            ### 🔬 연구 방법

            - **데이터**: 17개 시도, 제주 시군구 2곳의 남녀별 연령(0~100세+) 인구
            - **지표**: ① 여성 비율 ② 성비(여자 100명당 남자 수) ③ 연령대별 성비 곡선
            - **비교**: 전국 평균과 17개 시도 분포 속에서 제주의 위치 파악

            ### 💡 탐구 질문

            > 1. 제주도의 여성 비율은 전국에서 몇 위인가?
            > 2. 어느 연령대에서 여성이 가장 많은가?
            > 3. ‘삼다도’라는 말이 생긴 시대적 배경은 오늘날에도 유효한가?
            """
        )

    with col2:
        # 핵심 수치 미리보기
        jeju_row = sido[sido["name"] == "제주특별자치도"].iloc[0]
        st.markdown("#### 한눈에 보기")
        st.metric("제주도 총인구", f"{int(jeju_row['총인구']):,} 명")
        st.metric("여성 비율", f"{jeju_row['여성비율']:.2f} %")
        st.metric("성비 (여 100명당 남)", f"{jeju_row['성비']:.2f}")
        rank = (sido["여성비율"].rank(ascending=False).loc[jeju_row.name])
        st.metric("전국 17개 시도 중 여성비율 순위", f"{int(rank)} 위")
        st.markdown(
            '<div class="data-caption">※ 본 대시보드의 모든 수치는 위 데이터에서 직접 계산되었습니다.</div>',
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════════════════════════════════
# 1. 가설
# ════════════════════════════════════════════════════════════════════════════
elif section == "1. 가설 설정":
    st.markdown('<div class="report-title">1. 가설 설정</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="report-subtitle">‘삼다도’라는 표현을 데이터로 검증 가능한 형태로 바꾸기</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### 🪨 ‘삼다(三多)’의 세 가지 요소

        | 요소 | 의미 | 데이터 검증 가능성 |
        |------|------|---------------------|
        | **돌** | 화산섬이라 현무암이 흔하다 | ❌ 인구 데이터로는 불가 (지질 자료 필요) |
        | **바람** | 해풍이 강하다 | ❌ 인구 데이터로는 불가 (기상 자료 필요) |
        | **여자** | 남자보다 여자가 많다 | ✅ **인구 통계로 검증 가능** |

        ### 📜 가설 (Hypothesis)
        """
    )

    st.markdown(
        """
        <div class="hypothesis-box">
        <b>H1 (귀무가설, H₀)</b> — 제주도의 여성 비율은 다른 시도와 비슷하다 (혹은 더 낮다).<br>
        <b>H2 (대립가설, H₁)</b> — 제주도의 여성 비율은 전국 17개 시도 중 유의미하게 <b>상위권</b>에 속한다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### 🧭 판단 기준

        ‘삼다도’라는 표현이 통념대로 사실이라면, 적어도 다음 중 **하나 이상**은 성립해야 한다.

        1. 제주도의 전체 여성 비율이 **17개 시도 중 상위 3위 이내**
        2. 특정 연령대(예: 청장년 20~59세)에서 여성이 **눈에 띄게 많음**
        3. 제주 내부(제주시·서귀포시) 모두에서 여성 우세 경향이 나타남

        세 조건 모두 충족하지 못한다면, 적어도 **‘오늘날의 인구 구조’ 관점에서는** 통념을 그대로 받아들이기 어렵다고 판단한다.
        """
    )

# ════════════════════════════════════════════════════════════════════════════
# 2. 시도별 여성 비율
# ════════════════════════════════════════════════════════════════════════════
elif section == "2. 검증① 시도별 여성 비율":
    st.markdown('<div class="report-title">2. 검증 ① — 17개 시도 여성 비율 비교</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="report-subtitle">제주도는 전국에서 몇 번째로 여성이 많은 지역일까?</div>',
        unsafe_allow_html=True,
    )

    ranked = sido.sort_values("여성비율", ascending=False).reset_index(drop=True)
    ranked["순위"] = ranked.index + 1
    jeju_rank = int(ranked[ranked["name"] == "제주특별자치도"]["순위"].iloc[0])
    jeju_ratio = float(ranked[ranked["name"] == "제주특별자치도"]["여성비율"].iloc[0])
    top1_name = ranked.iloc[0]["name"]
    top1_ratio = ranked.iloc[0]["여성비율"]

    # 상단 핵심 수치
    c1, c2, c3 = st.columns(3)
    c1.metric("제주 여성 비율", f"{jeju_ratio:.2f}%")
    c2.metric("전국 17개 시도 중 순위", f"{jeju_rank}위 / 17")
    c3.metric(f"1위 ({top1_name})", f"{top1_ratio:.2f}%", delta=f"{top1_ratio-jeju_ratio:+.2f}p")

    # 막대그래프
    colors = [COLOR_JEJU if n == "제주특별자치도" else COLOR_OTHER for n in ranked["name"]]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=ranked["여성비율"],
            y=ranked["name"],
            orientation="h",
            marker=dict(color=colors, line=dict(color="#3a3a3a", width=0.5)),
            text=[f"{v:.2f}%" for v in ranked["여성비율"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>여성비율: %{x:.2f}%<extra></extra>",
        )
    )
    fig.add_vline(x=50, line_dash="dash", line_color="#b8862f", annotation_text="남녀 균형선 (50%)")
    fig.update_layout(
        title=dict(text="시도별 여성 비율 (전체 인구 기준)", font=dict(size=18)),
        xaxis=dict(title="여성 비율 (%)", range=[47.5, 52.5]),
        yaxis=dict(title="", autorange="reversed"),
        height=620,
        plot_bgcolor="#fafaf7",
        paper_bgcolor="#fafaf7",
        margin=dict(l=20, r=80, t=60, b=40),
        font=dict(family="Gowun Dodum"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"""
        <div class="finding-box">
        <span class="finding-label">발 견</span>
        <b>제주도의 여성 비율은 {jeju_ratio:.2f}%로 17개 시도 중 {jeju_rank}위이다.</b>
        이는 거의 정확히 <b>남녀 1:1</b>에 가까운 수치이며, 1위인 {top1_name}({top1_ratio:.2f}%)이나
        부산(51.41%), 대구(51.04%) 같은 대도시보다 명확하게 <b>낮다</b>.<br><br>
        오히려 여성 비율 상위권은 모두 <b>대도시</b>(서울·부산·대구·광주)가 차지하고 있다.
        이는 청년기 여성의 도시 유입·잔류 경향, 그리고 평균 수명 차이로 인한 고령 여성 인구가
        도시에 집중된 결과로 해석된다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### 🔍 시도별 데이터 표 (정렬: 여성 비율 내림차순)
        """
    )
    show = ranked[["순위", "name", "총인구", "남", "여", "여성비율", "성비"]].copy()
    show.columns = ["순위", "행정구역", "총인구", "남", "여", "여성비율(%)", "성비(여100당남)"]
    st.dataframe(
        show.style.format(
            {
                "총인구": "{:,.0f}",
                "남": "{:,.0f}",
                "여": "{:,.0f}",
                "여성비율(%)": "{:.2f}",
                "성비(여100당남)": "{:.2f}",
            }
        ).background_gradient(subset=["여성비율(%)"], cmap="RdYlGn_r"),
        use_container_width=True,
        height=640,
    )

# ════════════════════════════════════════════════════════════════════════════
# 3. 연령대별 성비
# ════════════════════════════════════════════════════════════════════════════
elif section == "3. 검증② 연령대별 성비":
    st.markdown('<div class="report-title">3. 검증 ② — 연령대별 성비 곡선</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="report-subtitle">‘여자가 많다’는 특정 연령대에서라도 사실일까?</div>',
        unsafe_allow_html=True,
    )

    # 비교 대상 선택
    compare_options = sorted(sido["name"].tolist())
    default_idx = [compare_options.index("서울특별시"), compare_options.index("전라남도")]
    chosen = st.multiselect(
        "비교할 시도를 선택하세요 (제주는 항상 표시)",
        options=[n for n in compare_options if n != "제주특별자치도"],
        default=[compare_options[i] for i in default_idx if compare_options[i] != "제주특별자치도"],
    )
    targets = ["제주특별자치도"] + chosen

    ages = list(range(0, 101))
    fig = go.Figure()
    palette = ["#2d3e2d", "#5b7a8a", "#c97b63", "#b8862f", "#7d6b8c", "#4a5568"]
    for i, name in enumerate(targets):
        row = sido[sido["name"] == name].iloc[0]
        male_v = np.array([row[f"{PREFIX}_남_{a}세"] for a in ages], dtype=float)
        female_v = np.array([row[f"{PREFIX}_여_{a}세"] for a in ages], dtype=float)
        # 0 division 방지
        ratio = np.where(female_v > 0, male_v / female_v * 100, np.nan)
        fig.add_trace(
            go.Scatter(
                x=ages,
                y=ratio,
                mode="lines",
                name=name,
                line=dict(
                    width=3.5 if name == "제주특별자치도" else 1.8,
                    color=palette[i % len(palette)],
                ),
                hovertemplate=f"<b>{name}</b><br>%{{x}}세<br>성비: %{{y:.1f}}<extra></extra>",
            )
        )
    fig.add_hline(y=100, line_dash="dash", line_color="#b8862f", annotation_text="남녀 균형 (100)")
    fig.update_layout(
        title=dict(text="연령별 성비 (여자 100명당 남자 수)", font=dict(size=18)),
        xaxis=dict(title="연령(세)", dtick=10),
        yaxis=dict(title="성비 (남/여 × 100)", range=[20, 130]),
        height=520,
        plot_bgcolor="#fafaf7",
        paper_bgcolor="#fafaf7",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Gowun Dodum"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
        ### 📖 그래프 읽는 법
        - **100 이상** → 남자가 더 많은 연령대
        - **100 미만** → 여자가 더 많은 연령대 (선이 아래로 내려갈수록 ‘여초’ 심화)
        - 일반적으로 출생 시점에는 남아가 약간 더 많고(약 105), 고령으로 갈수록 평균 수명 차이로 인해 여성이 많아진다.
        """
    )

    # 제주 인구 피라미드
    st.markdown("### 🌋 제주도 인구 피라미드")
    jeju = sido[sido["name"] == "제주특별자치도"].iloc[0]
    male_v = [jeju[f"{PREFIX}_남_{a}세"] for a in ages]
    female_v = [jeju[f"{PREFIX}_여_{a}세"] for a in ages]

    fig2 = go.Figure()
    fig2.add_trace(
        go.Bar(
            y=ages, x=[-v for v in male_v], orientation="h", name="남",
            marker=dict(color=COLOR_MALE),
            hovertemplate="%{y}세 남<br>%{customdata:,}명<extra></extra>",
            customdata=male_v,
        )
    )
    fig2.add_trace(
        go.Bar(
            y=ages, x=female_v, orientation="h", name="여",
            marker=dict(color=COLOR_FEMALE),
            hovertemplate="%{y}세 여<br>%{x:,}명<extra></extra>",
        )
    )
    max_v = max(max(male_v), max(female_v))
    fig2.update_layout(
        barmode="overlay",
        bargap=0.05,
        title=dict(text="제주특별자치도 인구 피라미드 (2026.04)", font=dict(size=18)),
        xaxis=dict(
            title="인구수",
            tickvals=[-8000, -4000, 0, 4000, 8000],
            ticktext=["8천", "4천", "0", "4천", "8천"],
            range=[-max_v * 1.1, max_v * 1.1],
        ),
        yaxis=dict(title="연령(세)", dtick=10),
        height=560,
        plot_bgcolor="#fafaf7",
        paper_bgcolor="#fafaf7",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Gowun Dodum"),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 연령대 묶음 분석
    bands = {
        "0~19세 (유소년·청소년)": range(0, 20),
        "20~39세 (청년)": range(20, 40),
        "40~59세 (중년)": range(40, 60),
        "60~79세 (장년)": range(60, 80),
        "80세 이상 (노년)": list(range(80, 101)),
    }
    band_rows = []
    for label, rng in bands.items():
        m = sum(jeju[f"{PREFIX}_남_{a}세"] for a in rng)
        f = sum(jeju[f"{PREFIX}_여_{a}세"] for a in rng)
        band_rows.append(
            {"연령대": label, "남": m, "여": f, "여성비율(%)": f / (m + f) * 100, "성비": m / f * 100}
        )
    band_df = pd.DataFrame(band_rows)

    st.markdown("### 📊 제주도 연령대별 성비")
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.dataframe(
            band_df.style.format(
                {"남": "{:,.0f}", "여": "{:,.0f}", "여성비율(%)": "{:.2f}", "성비": "{:.2f}"}
            ).background_gradient(subset=["여성비율(%)"], cmap="RdYlGn_r"),
            use_container_width=True,
            hide_index=True,
        )
    with c2:
        max_band = band_df.loc[band_df["여성비율(%)"].idxmax()]
        st.markdown(
            f"""
            <div class="finding-box">
            <span class="finding-label">발 견</span>
            제주도에서 여성이 가장 우세한 연령대는 <b>{max_band['연령대']}</b>로,
            여성비율 <b>{max_band['여성비율(%)']:.2f}%</b>이다.<br><br>
            이는 모든 지역에서 공통으로 나타나는 <b>고령층 여성 우세 현상</b>일 뿐,
            제주만의 특징이 아니다. 청년·중년에서는 오히려 <b>남성이 더 많다</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════════════════════════════════
# 4. 제주 내부 비교
# ════════════════════════════════════════════════════════════════════════════
elif section == "4. 검증③ 제주 내부 들여다보기":
    st.markdown('<div class="report-title">4. 검증 ③ — 제주도 내부 들여다보기</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="report-subtitle">제주시와 서귀포시의 인구 구조는 어떻게 다른가?</div>',
        unsafe_allow_html=True,
    )

    # 시군구 비교
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=jeju_sigungu["short_name"],
            y=jeju_sigungu["남"],
            name="남",
            marker=dict(color=COLOR_MALE),
            text=[f"{v:,}" for v in jeju_sigungu["남"]],
            textposition="inside",
        )
    )
    fig.add_trace(
        go.Bar(
            x=jeju_sigungu["short_name"],
            y=jeju_sigungu["여"],
            name="여",
            marker=dict(color=COLOR_FEMALE),
            text=[f"{v:,}" for v in jeju_sigungu["여"]],
            textposition="inside",
        )
    )
    fig.update_layout(
        title=dict(text="제주시 vs 서귀포시 — 남녀 인구", font=dict(size=18)),
        barmode="group",
        height=380,
        plot_bgcolor="#fafaf7",
        paper_bgcolor="#fafaf7",
        yaxis=dict(title="인구수"),
        font=dict(family="Gowun Dodum"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 표
    show = jeju_sigungu[["short_name", "총인구", "남", "여", "여성비율"]].copy()
    show.columns = ["행정구역", "총인구", "남", "여", "여성비율(%)"]
    st.dataframe(
        show.style.format(
            {"총인구": "{:,.0f}", "남": "{:,.0f}", "여": "{:,.0f}", "여성비율(%)": "{:.2f}"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    # 읍면동 단위 분석 (선택)
    st.markdown("### 🏘️ 읍·면·동 단위로 더 깊이 보기")
    st.caption("제주 내에서 가장 여성 비율이 높은 읍·면·동은 어디일까?")

    eup = df[(df["level"] == "읍면동") & (df["name"].str.startswith("제주특별자치도"))].copy()
    eup["남"] = eup[MALE_TOTAL]
    eup["여"] = eup[FEMALE_TOTAL]
    eup["총인구"] = eup["남"] + eup["여"]
    eup = eup[eup["총인구"] > 500].copy()  # 너무 작은 단위 제외
    eup["여성비율"] = eup["여"] / eup["총인구"] * 100
    eup["short_name"] = eup["name"].str.replace("제주특별자치도 ", "", regex=False)

    top10 = eup.nlargest(10, "여성비율")[["short_name", "총인구", "여성비율"]]
    bot10 = eup.nsmallest(10, "여성비율")[["short_name", "총인구", "여성비율"]]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📈 여성 비율 높은 동네 TOP 10**")
        st.dataframe(
            top10.rename(columns={"short_name": "행정구역", "여성비율": "여성비율(%)"})
            .style.format({"총인구": "{:,.0f}", "여성비율(%)": "{:.2f}"})
            .background_gradient(subset=["여성비율(%)"], cmap="Reds"),
            hide_index=True,
            use_container_width=True,
        )
    with c2:
        st.markdown("**📉 여성 비율 낮은 동네 BOTTOM 10**")
        st.dataframe(
            bot10.rename(columns={"short_name": "행정구역", "여성비율": "여성비율(%)"})
            .style.format({"총인구": "{:,.0f}", "여성비율(%)": "{:.2f}"})
            .background_gradient(subset=["여성비율(%)"], cmap="Blues_r"),
            hide_index=True,
            use_container_width=True,
        )

    st.markdown(
        f"""
        <div class="finding-box">
        <span class="finding-label">발 견</span>
        제주 내부에서도 여성 비율은 동네마다 큰 차이를 보인다.
        가장 여성이 많은 곳은 <b>{top10.iloc[0]['short_name']}</b>({top10.iloc[0]['여성비율']:.2f}%),
        가장 적은 곳은 <b>{bot10.iloc[0]['short_name']}</b>({bot10.iloc[0]['여성비율']:.2f}%)다.<br><br>
        이 차이는 산업 구성(농어업·관광·군부대 등)과 고령화 정도에서 비롯된 것으로 추정되며,
        ‘제주=여자가 많은 섬’이라는 단일한 명제로 묶기 어려운 <b>내부 다양성</b>을 보여준다.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════════════════════════════════
# 5. 재해석
# ════════════════════════════════════════════════════════════════════════════
elif section == "5. 가설 재해석":
    st.markdown('<div class="report-title">5. 가설의 재해석</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="report-subtitle">데이터가 ‘아니다’라고 말할 때, 우리는 통념을 어떻게 다시 읽어야 할까?</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### 🤔 왜 ‘여자가 많은 섬’이라는 말이 생겼을까?

        앞선 세 가지 검증을 종합하면, **오늘날 인구 통계에서는** ‘여자가 많다’는 명제가 성립하지 않는다.
        그런데도 ‘삼다도’라는 표현은 왜 지금까지 살아남았을까? 몇 가지 가능한 해석을 제시한다.

        #### ① 역사적 시점의 차이
        ‘삼다도’는 **오래 전부터 전해 내려온 표현**이다. 과거 제주에서는 거친 바다에서의 어업 사고,
        한국전쟁 등으로 **성인 남성 인구가 상대적으로 적었던 시기**가 있었다.
        그 시기의 인상이 표현으로 굳어졌을 가능성이 있다.

        #### ② ‘보이는 노동’의 성별 편향
        제주의 대표적인 노동 풍경은 **해녀**다. 바다에서 일하는 여성의 모습이 강하게 각인되면서,
        실제 인구 비율보다 ‘여자가 많아 보이는’ 인상이 형성되었을 수 있다.

        #### ③ 표현의 운율적 완성
        ‘돌·바람·여자’는 세 음절씩 균형 잡힌 운율을 가진 표현이다.
        엄밀한 통계가 아니라 **섬의 풍경을 압축한 시적 표현**으로 이해할 여지가 있다.

        ### 🔄 가설의 수정

        > 원가설: “제주도는 여자가 많은 섬이다.”
        >
        > **수정가설:** “제주도는 *역사적으로* 여성 노동이 두드러지게 드러나는 섬이었으며,
        > ‘삼다도’는 통계적 사실이 아니라 **문화적 인상의 표현**이다.”
        """
    )

    st.markdown(
        """
        <div class="hypothesis-box">
        ✨ <b>탐구의 교훈</b><br>
        통념이 데이터로 입증되지 않았다고 해서, 그 통념이 무의미한 것은 아니다.
        다만 “이 표현은 어느 시대, 어떤 맥락에서 만들어졌는가?”를 묻는 것이
        데이터 분석가의 또 다른 역할이다.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════════════════════════════════
# 6. 결론
# ════════════════════════════════════════════════════════════════════════════
elif section == "6. 결론 및 제언":
    st.markdown('<div class="report-title">6. 결론 및 제언</div>', unsafe_allow_html=True)

    jeju_row = sido[sido["name"] == "제주특별자치도"].iloc[0]
    ranked = sido.sort_values("여성비율", ascending=False).reset_index(drop=True)
    jeju_rank = int(ranked[ranked["name"] == "제주특별자치도"].index[0]) + 1

    st.markdown(
        f"""
        ### 📌 핵심 결론

        1. **오늘날 제주도의 여성 비율은 {jeju_row['여성비율']:.2f}%로 17개 시도 중 {jeju_rank}위**이다.
           이는 거의 정확히 남녀 1:1 수준이며, 서울·부산·대구 같은 대도시보다 오히려 낮다.
        2. **모든 연령대를 통틀어, 제주도에서 여성이 특별히 많은 구간은 없다.**
           고령층 여성 우세는 평균 수명 차이에 의한 전국 공통 현상이다.
        3. **제주 내부에서도 여성 비율은 동네마다 크게 다르다.** 단일 명제로 묶을 수 없다.

        ⇒ 따라서 **인구 데이터 관점에서 ‘삼다도(여자가 많다)’ 가설은 기각된다.**

        ### 💬 제언

        - **통계 리터러시**: 오래된 통념일수록 “지금도 사실인가?”를 의식적으로 묻는 습관이 필요하다.
        - **데이터의 시점성**: 같은 명제도 100년 전·50년 전·현재의 결론이 다를 수 있다.
          ‘삼다도’ 표현이 만들어진 시기의 인구 자료를 함께 분석하면 더 풍부한 결론이 가능할 것이다.
        - **문화적 의미의 가치**: 데이터로 입증되지 않더라도, ‘삼다도’는 제주를 압축한
          **문화적 상징**으로서 여전히 의미가 있다. 데이터와 문화는 대립 관계가 아니다.

        ### 🔭 후속 탐구 아이디어

        - 1960~70년대 제주도 인구 통계와 비교해 ‘삼다도’ 명제의 시대별 변화 추적
        - 기상자료로 ‘바람 많은 섬’ 검증 (풍속 데이터 활용)
        - 지질자료로 ‘돌 많은 섬’ 검증 (화산암 분포)
        - 해녀 인구의 시계열 변화 분석
        """
    )

    st.markdown(
        """
        <div class="finding-box" style="border-left:6px solid #2d3e2d;">
        <span class="finding-label" style="background:#b8862f;">최종 판정</span>
        <b style="font-size:1.15rem;">제주도가 ‘여자가 많은 섬’이라는 통념은,
        2026년 4월 주민등록 인구 데이터로는 <span style="color:#a94442;">입증되지 않았다.</span></b><br><br>
        그러나 ‘삼다도’라는 표현은 통계적 사실이 아니라 <b>제주의 역사·노동·풍경을 응축한 문화적 표현</b>으로
        여전히 의미를 갖는다. 데이터가 통념을 부정할 때, 우리는 그 통념이 만들어진 <b>맥락</b>으로 시선을 옮길 수 있다.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════════════════════════════════
# 원자료
# ════════════════════════════════════════════════════════════════════════════
elif section == "📊 원자료 살펴보기":
    st.markdown('<div class="report-title">📊 원자료 살펴보기</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="report-subtitle">분석에 사용된 데이터를 직접 확인하고 다운로드할 수 있습니다.</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["시도 단위", "제주 시군구", "전체 원본"])

    with tab1:
        show = sido[["name", "총인구", "남", "여", "여성비율", "성비"]].copy()
        show.columns = ["행정구역", "총인구", "남", "여", "여성비율(%)", "성비"]
        st.dataframe(
            show.style.format(
                {"총인구": "{:,.0f}", "남": "{:,.0f}", "여": "{:,.0f}",
                 "여성비율(%)": "{:.2f}", "성비": "{:.2f}"}
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "시도 데이터 CSV 다운로드",
            data=show.to_csv(index=False).encode("utf-8-sig"),
            file_name="시도별_인구_2026_04.csv",
            mime="text/csv",
        )

    with tab2:
        eup = df[(df["level"] == "읍면동") & (df["name"].str.startswith("제주특별자치도"))].copy()
        eup["남"] = eup[MALE_TOTAL]
        eup["여"] = eup[FEMALE_TOTAL]
        eup["총인구"] = eup["남"] + eup["여"]
        eup["여성비율"] = eup["여"] / eup["총인구"] * 100
        eup["행정구역"] = eup["name"].str.replace("제주특별자치도 ", "", regex=False)
        show = eup[["행정구역", "총인구", "남", "여", "여성비율"]].copy()
        show.columns = ["행정구역", "총인구", "남", "여", "여성비율(%)"]
        st.dataframe(
            show.style.format(
                {"총인구": "{:,.0f}", "남": "{:,.0f}", "여": "{:,.0f}", "여성비율(%)": "{:.2f}"}
            ),
            use_container_width=True,
            hide_index=True,
            height=600,
        )

    with tab3:
        st.caption(f"원본 데이터: {df.shape[0]:,}행 × {df.shape[1]:,}열")
        st.dataframe(df.head(50), use_container_width=True, height=400)
        st.caption("※ 너무 커서 상위 50행만 표시합니다.")

# 푸터
st.markdown("---")
st.caption(
    "탐구 보고서 대시보드 · 데이터: 행정안전부 주민등록 인구통계(2026.04) · "
    "분석 도구: Python · Streamlit · Plotly"
)
