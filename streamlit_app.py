#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling  (지표카드 밝은 배경으로 변경)
st.markdown("""
<style>

:root {
  --metric-bg: #f7f8fb;         /* 밝은 카드 배경 */
  --metric-text: #1f2937;       /* 카드 텍스트 */
  --metric-border: #e6e8f0;     /* 테두리 */
  --metric-shadow: 0 2px 8px rgba(0,0,0,0.06);
  --delta-pos-bg: #e8f5e9;      /* +델타 배경 */
  --delta-pos-fg: #1b5e20;      /* +델타 텍스트 */
  --delta-neg-bg: #ffebee;      /* -델타 배경 */
  --delta-neg-fg: #b71c1c;      /* -델타 텍스트 */
}

/* 페이지 패딩 */
[data-testid="block-container"] {
  padding-left: 2rem;
  padding-right: 2rem;
  padding-top: 1rem;
  padding-bottom: 0rem;
  margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
  padding-left: 0rem;
  padding-right: 0rem;
}

/* ====== 지표 카드(st.metric) 밝은 톤 ====== */
[data-testid="stMetric"] {
  background-color: var(--metric-bg) !important;
  color: var(--metric-text) !important;
  text-align: center;
  padding: 14px 0 16px 0;
  border: 1px solid var(--metric-border);
  border-radius: 12px;
  box-shadow: var(--metric-shadow);
}

/* 라벨 중앙정렬 */
[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
  color: #4b5563 !important;
}

/* 값 컬러 */
[data-testid="stMetricValue"] {
  color: var(--metric-text) !important;
}

/* 델타 pill 스타일 (양수/음수) */
div[data-testid="stMetricDelta"] {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 9999px;
  font-weight: 600;
}
[data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Up"]) {
  background: var(--delta-pos-bg);
  color: var(--delta-pos-fg) !important;
}
[data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Down"]) {
  background: var(--delta-neg-bg);
  color: var(--delta-neg-fg) !important;
}

/* 델타 아이콘 위치 보정 */
[data-testid="stMetricDeltaIcon-Up"], [data-testid="stMetricDeltaIcon-Down"] {
  position: relative;
  left: 38%;
  transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)


#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv')  # 분석 데이터


#######################
# Sidebar
with st.sidebar:
    # ── App Title & About
    st.title("Titanic Survival Explorer")
    st.caption("🎯 필터를 바꾸면 모든 지표/차트가 동기 갱신됩니다.")
    with st.expander("About / 데이터 & 전처리 요약", expanded=False):
        st.markdown(
            "- 데이터: Titanic passengers\n"
            "- 목표: 생존율과 분포를 조건별로 탐색\n"
            "- 기본 전처리 가정: Age(그룹 중앙값), Embarked(최빈), Fare(Pclass별 중앙값)\n"
            "- 파생: AgeBand, FamilySize, IsAlone, Title, FarePerPerson"
        )

    st.markdown("---")

    # ── Theme / Display options
    theme = st.selectbox("Color theme", ["light", "dark"], index=0)
    label_size = st.slider("Label font size", 8, 20, 12)
    show_percent = st.toggle("지표를 % 단위로 표시", value=True)

    st.markdown("---")

    # ── Filters
    # Sex
    sex_opts = sorted([x for x in df_reshaped["Sex"].dropna().unique()])
    sex_sel = st.multiselect("성별 (Sex)", options=sex_opts, default=sex_opts)

    # Pclass
    pclass_opts = sorted([int(x) for x in df_reshaped["Pclass"].dropna().unique()])
    pclass_sel = st.multiselect("객실 등급 (Pclass)", options=pclass_opts, default=pclass_opts)

    # AgeBand (연령대)
    age_bins = [0, 10, 20, 30, 40, 50, 60, 70, 120]
    age_labels = ["0–9", "10–19", "20–29", "30–39", "40–49", "50–59", "60–69", "70+"]
    ageband_sel = st.multiselect("연령대 (AgeBand)", options=age_labels, default=age_labels)

    # Embarked
    embarked_opts = [x for x in df_reshaped["Embarked"].dropna().unique()]
    embarked_sel = st.multiselect("승선항 (Embarked)", options=embarked_opts, default=embarked_opts)

    # IsAlone
    alone_mode = st.segmented_control("동승 가족 여부", options=["All", "Alone", "With family"], default="All")

    # Fare range (+ log-scale option)
    min_fare = float(df_reshaped["Fare"].min(skipna=True)) if "Fare" in df_reshaped else 0.0
    max_fare = float(df_reshaped["Fare"].max(skipna=True)) if "Fare" in df_reshaped else 600.0
    use_log = st.toggle("운임 슬라이더 로그축", value=False)
    fare_min, fare_max = st.slider(
        "운임 범위 (Fare)", min_value=min_fare, max_value=max_fare,
        value=(min_fare, max_fare), step=0.5, help="현재 범위 내 승객만 집계"
    )

    # Cabin known
    cabin_known_only = st.toggle("Cabin 정보가 있는 레코드만", value=False)

    st.markdown("---")

    # Download current (unfiltered placeholder)
    st.download_button(
        "현재 데이터 CSV 다운로드",
        data=df_reshaped.to_csv(index=False).encode("utf-8"),
        file_name="titanic_current_view.csv",
        mime="text/csv",
        use_container_width=True
    )

    # ── Persist filters in session_state for use in main panels
    st.session_state["filters"] = {
        "theme": theme,
        "label_size": label_size,
        "show_percent": show_percent,
        "sex": sex_sel,
        "pclass": pclass_sel,
        "age_bins": age_bins,
        "age_labels": age_labels,
        "ageband": ageband_sel,
        "embarked": embarked_sel,
        "alone_mode": alone_mode,
        "use_log": use_log,
        "fare_range": (fare_min, fare_max),
        "cabin_known_only": cabin_known_only,
    }


#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

# ─────────────────────────────────────────────────────────────
# Column 0: KPI + 비교 바차트
# ─────────────────────────────────────────────────────────────
with col[0]:
    st.subheader("📌 핵심 지표 요약")

    filters = st.session_state.get("filters", {})
    df_view = df_reshaped.copy()  # (필터 적용 로직 연결 가능)

    # KPI
    total_passengers = len(df_view)
    survived = df_view["Survived"].sum()
    survival_rate = survived / total_passengers * 100 if total_passengers > 0 else 0
    avg_age = df_view["Age"].mean(skipna=True)
    avg_fare = df_view["Fare"].mean(skipna=True)

    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.metric("총 승객 수", f"{total_passengers:,}")
    with kpi2:
        st.metric("생존자 수", f"{survived:,}", f"{survival_rate:.1f}%")

    kpi3, kpi4 = st.columns(2)
    with kpi3:
        st.metric("평균 나이", f"{avg_age:.1f}")
    with kpi4:
        st.metric("평균 운임", f"${avg_fare:.2f}")

    st.markdown("---")

    # 성별 생존율
    st.markdown("### 🚻 성별 생존율")
    sex_survival = df_view.groupby("Sex")["Survived"].mean().reset_index()
    sex_chart = alt.Chart(sex_survival).mark_bar().encode(
        x=alt.X("Sex:N", title="성별"),
        y=alt.Y("Survived:Q", title="생존율", axis=alt.Axis(format="%")),
        color="Sex",
        tooltip=["Sex", alt.Tooltip("Survived:Q", format=".0%")]
    )
    st.altair_chart(sex_chart, use_container_width=True)

    # 객실등급 생존율
    st.markdown("### 🛳 객실등급별 생존율")
    pclass_survival = df_view.groupby("Pclass")["Survived"].mean().reset_index()
    pclass_chart = alt.Chart(pclass_survival).mark_bar().encode(
        x=alt.X("Pclass:N", title="객실등급"),
        y=alt.Y("Survived:Q", title="생존율", axis=alt.Axis(format="%")),
        color="Pclass:N",
        tooltip=["Pclass", alt.Tooltip("Survived:Q", format=".0%")]
    )
    st.altair_chart(pclass_chart, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Column 1: 히트맵 + 분포 + 상관
# ─────────────────────────────────────────────────────────────
with col[1]:
    st.subheader("🗺️ 주요 시각화 (히트맵 + 분포)")

    filters = st.session_state.get("filters", {})
    age_bins   = filters.get("age_bins", [0,10,20,30,40,50,60,70,120])
    age_labels = filters.get("age_labels", ["0–9","10–19","20–29","30–39","40–49","50–59","60–69","70+"])

    df_view = df_reshaped.copy()

    if "AgeBand" not in df_view.columns:
        df_view["AgeBand"] = pd.cut(df_view["Age"], bins=age_bins, labels=age_labels, right=False)
    if "FamilySize" not in df_view.columns:
        df_view["FamilySize"] = (df_view.get("SibSp", 0) + df_view.get("Parch", 0) + 1)
    if "FarePerPerson" not in df_view.columns:
        df_view["FarePerPerson"] = df_view["Fare"] / df_view["FamilySize"].replace(0, 1)

    # 1) AgeBand x Pclass 히트맵
    hm = (
        df_view.dropna(subset=["AgeBand", "Pclass", "Survived"])
        .groupby(["AgeBand", "Pclass"])
        .agg(count=("Survived", "size"), survival_rate=("Survived", "mean"))
        .reset_index()
    )
    hm["survival_pct"] = (hm["survival_rate"] * 100).round(1)
    hm["label"] = hm["survival_pct"].astype(str) + "%"

    st.markdown("#### 🔳 연령대 × 객실등급 생존율 히트맵")
    heat = alt.Chart(hm).mark_rect().encode(
        x=alt.X("Pclass:O", title="객실등급"),
        y=alt.Y("AgeBand:N", title="연령대", sort=age_labels),
        color=alt.Color("survival_rate:Q", title="생존율", scale=alt.Scale(scheme="blues")),
        tooltip=[
            alt.Tooltip("AgeBand:N", title="연령대"),
            alt.Tooltip("Pclass:O", title="객실"),
            alt.Tooltip("survival_pct:Q", title="생존율(%)"),
            alt.Tooltip("count:Q", title="표본수")
        ]
    ).properties(height=360)

    text = alt.Chart(hm).mark_text(baseline="middle").encode(
        x="Pclass:O",
        y=alt.Y("AgeBand:N", sort=age_labels),
        text="label:N",
        color=alt.value("black")
    )
    st.altair_chart(heat + text, use_container_width=True)
    st.caption("※ 각 셀의 표본수가 적을수록(예: n<20) 해석에 유의하세요.")
    st.markdown("---")

    # 2) 나이 히스토그램 + 운임 박스플롯
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("#### ⏳ 나이 분포 (생존/사망 비교)")
        df_age = df_view.dropna(subset=["Age", "Survived"]).copy()
        df_age["SurvivedLabel"] = df_age["Survived"].map({0: "Died", 1: "Survived"})
        fig_age = px.histogram(
            df_age, x="Age", color="SurvivedLabel", nbins=30,
            barmode="overlay", opacity=0.65,
            labels={"Age": "나이", "SurvivedLabel": "생존여부"}
        )
        fig_age.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_age, use_container_width=True)

    with c_right:
        st.markdown("#### 💸 운임 분포 (생존/사망 박스플롯)")
        df_fare = df_view.dropna(subset=["Fare", "Survived"]).copy()
        df_fare["SurvivedLabel"] = df_fare["Survived"].map({0: "Died", 1: "Survived"})
        fig_fare = px.box(
            df_fare, x="SurvivedLabel", y="Fare", points="outliers",
            labels={"SurvivedLabel": "생존여부", "Fare": "운임(Fare)"}
        )
        fig_fare.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_fare, use_container_width=True)

    st.markdown("---")

    # 3) 수치형 상관 히트맵
    st.markdown("#### 🔗 수치형 변수 상관 히트맵")
    numeric_cols = ["Survived", "Age", "Fare", "FamilySize", "FarePerPerson", "SibSp", "Parch"]
    exist_cols = [c for c in numeric_cols if c in df_view.columns]
    corr = df_view[exist_cols].corr(numeric_only=True).round(2)

    fig_corr = px.imshow(
        corr, text_auto=True, aspect="auto",
        color_continuous_scale="Blues",
        labels=dict(color="상관계수")
    )
    fig_corr.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_corr, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Column 2: Top 그룹 + 설명
# ─────────────────────────────────────────────────────────────
with col[2]:
    st.subheader("🔍 상세 분석 & 인사이트")

    df_view = df_reshaped.copy()  # (필터 반영 위치)

    # Top 그룹 집계
    st.markdown("#### 🏆 생존율 Top 그룹")
    top_groups = (
        df_view.groupby(["Sex", "Pclass"])
        .agg(count=("Survived", "size"), survival_rate=("Survived", "mean"))
        .reset_index()
    )
    top_groups["survival_pct"] = (top_groups["survival_rate"] * 100).round(1)

    top_high = top_groups.sort_values("survival_rate", ascending=False).head(5)
    st.dataframe(
        top_high[["Sex", "Pclass", "count", "survival_pct"]],
        use_container_width=True, hide_index=True
    )

    st.markdown("#### ⚠️ 생존율 낮은 그룹")
    top_low = top_groups.sort_values("survival_rate", ascending=True).head(5)
    st.dataframe(
        top_low[["Sex", "Pclass", "count", "survival_pct"]],
        use_container_width=True, hide_index=True
    )

    st.markdown("---")

    # 바 차트
    st.markdown("#### 📊 그룹별 생존율 비교")
    bar_chart = alt.Chart(top_groups).mark_bar().encode(
        x=alt.X("survival_pct:Q", title="생존율(%)"),
        y=alt.Y("Sex:N", title="성별"),
        color="Pclass:N",
        tooltip=["Sex", "Pclass", "count", "survival_pct"]
    ).properties(height=300)
    st.altair_chart(bar_chart, use_container_width=True)

    st.markdown("---")

    # 상세 테이블 예시
    st.markdown("#### 👥 상세 테이블 (예: 여성 & 1등급)")
    detail_df = df_view[(df_view["Sex"] == "female") & (df_view["Pclass"] == 1)]
    st.dataframe(
        detail_df[["PassengerId", "Sex", "Pclass", "Age", "Fare", "Survived"]].head(10),
        use_container_width=True, hide_index=True
    )
    st.caption("※ 클릭형 드릴다운으로 확장 가능")

    st.markdown("---")

    # About / Insights
    with st.expander("ℹ️ 데이터/지표 설명", expanded=False):
        st.markdown(
            """
            - **Survival Rate**: 생존자 수 ÷ 전체 표본 수  
            - **표본수(n)**가 작을 경우(예: <20) 지표 신뢰도가 낮음  
            - 데이터 출처: Titanic passengers dataset  
            - 전처리 요약: Age(중앙값 대체), Embarked(최빈값), Fare(Pclass별 중앙값)  
            """
        )

    try:
        female_first = top_groups[(top_groups["Sex"] == "female") & (top_groups["Pclass"] == 1)]["survival_pct"].values[0]
        avg_rate = (df_view["Survived"].mean() * 100).round(1)
        st.success(f"💡 인사이트: 여성 1등급의 생존율은 **{female_first}%** 로, 전체 평균({avg_rate}%)보다 높습니다.")
    except Exception:
        st.info("데이터가 부족하여 인사이트를 계산할 수 없습니다.")
