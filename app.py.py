import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────
@st.cache_data
def load_data(path: str = "seoul_temperature.csv") -> pd.DataFrame:
    df = pd.read_csv(path)

    # 날짜 컬럼의 탭 문자 제거 후 정리
    df["날짜"] = df["날짜"].astype(str).str.replace("\t", "", regex=False).str.strip()

    # 날짜 → datetime → 연도 추출
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["연도"] = df["날짜"].dt.year

    # 기온 컬럼을 숫자로 변환
    for col in ["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["연도", "평균기온(℃)"])

# ─────────────────────────────────────────────
# 연도별 집계 + 5년 이동평균
# ─────────────────────────────────────────────
@st.cache_data
def compute_yearly(df: pd.DataFrame) -> pd.DataFrame:
    yearly = (
        df.groupby("연도")["평균기온(℃)"].mean()
        .reset_index()
        .rename(columns={"평균기온(℃)": "평균기온"})
    )
    yearly["5년_이동평균"] = yearly["평균기온"].rolling(window=5, min_periods=1).mean()
    return yearly

# ─────────────────────────────────────────────
# Streamlit 앱
# ─────────────────────────────────────────────
def main() -> None:
    st.set_page_config(page_title="서울 기온 대시보드", layout="wide")
    st.title("🌡️ 서울 기온 대시보드")
    st.caption("서울 지점별 일평균 기온을 연도별로 시각화합니다.")

    df = load_data()
    yearly = compute_yearly(df)

    # ── 사이드바: 연도 범위 슬라이더 ──
    min_year = int(yearly["연도"].min())
    max_year = int(yearly["연도"].max())

    st.sidebar.title("📅 설정")
    start_year, end_year = st.sidebar.slider(
        "연도 범위",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1,
        format="%d년",
    )

    # ── 선택 구간 필터링 ──
    mask = (yearly["연도"] >= start_year) & (yearly["연도"] <= end_year)
    sub = yearly[mask]

    orig_mask = (df["연도"] >= start_year) & (df["연도"] <= end_year)
    orig_sub = df[orig_mask]

    # ── 통계 카드 ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("평균 기온 (연평균)", f"{sub['평균기온'].mean():.2f} ℃")
    with c2:
        st.metric("최고 기온 (연평균 중 최대)", f"{sub['평균기온'].max():.2f} ℃")
    with c3:
        st.metric("최저 기온 (연평균 중 최소)", f"{sub['평균기온'].min():.2f} ℃")

    # ── Plotly 그래프 ──
    fig = go.Figure()

    # 연도별 평균기온 (꺾은선)
    fig.add_trace(go.Scatter(
        x=sub["연도"],
        y=sub["평균기온"],
        mode="lines+markers",
        name="연도별 평균기온",
        line=dict(color="#1f77b4", width=2.5),
        marker=dict(size=8, symbol="circle"),
    ))

    # 5년 이동평균 (겹쳐서 표시)
    fig.add_trace(go.Scatter(
        x=sub["연도"],
        y=sub["5년_이동평균"],
        mode="lines",
        name="5년 이동평균",
        line=dict(color="#d62728", width=3, dash="dash"),
    ))

    fig.update_layout(
        title=dict(
            text=f"서울 연도별 평균기온  ({start_year}년 ~ {end_year}년)",
            x=0.02,
            y=0.97,
            xanchor="left",
            yanchor="top",
        ),
        xaxis_title="연도",
        yaxis_title="평균기온 (℃)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(yanchor="top", y=1.12, xanchor="left", x=0),
        margin=dict(l=40, r=20, t=80, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── 원본 데이터 미리보기 ──
    with st.expander("📋 원본 데이터 미리보기"):
        st.dataframe(
            orig_sub[["날짜", "지점", "평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]],
            use_container_width=True,
            hide_index=True,
        )

if __name__ == "__main__":
    main()
