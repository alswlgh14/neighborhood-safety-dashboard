import pandas as pd
import plotly.graph_objects as go
import streamlit as st

YEARS = [2022, 2023, 2024, 2025]
GROUPS = {
    "프리미엄": ["메르세데스-벤츠", "BMW", "아우디", "렉서스", "볼보", "캐딜락", "링컨", "폴스타"],
    "럭셔리": ["포르쉐", "랜드로버", "재규어", "마세라티"],
    "플래그십·슈퍼카": ["롤스로이스", "벤틀리", "페라리", "람보르기니"],
}
GROUP_COLORS = {"프리미엄": "#75AAD7", "럭셔리": "#E4A569", "플래그십·슈퍼카": "#B59ADD"}
BRAND_GROUP = {brand: group for group, brands in GROUPS.items() for brand in brands}
# KAIDA annual releases. None means that the release did not report a value.
REGISTRATIONS = {
    "메르세데스-벤츠": [80976, 76697, 66400, 68467],
    "BMW": [78545, 77395, 73754, 77127],
    "아우디": [21402, 17868, 9304, 11001],
    "렉서스": [7592, 13561, 13969, 14891],
    "볼보": [14431, 17018, 15051, 14903],
    "캐딜락": [977, 975, 666, 785],
    "링컨": [2548, 1658, 2189, 1127],
    "폴스타": [2794, 1654, 800, 2957],
    "포르쉐": [8963, 11355, 8284, 10746],
    "랜드로버": [3113, 5019, 4437, 5255],
    "재규어": [163, 54, None, None],
    "마세라티": [554, 434, 251, 304],
    "롤스로이스": [234, 276, 183, 166],
    "벤틀리": [775, 810, 400, 393],
    "페라리": [None, None, None, 354],
    "람보르기니": [403, 431, 487, 478],
}
COUNTS = pd.DataFrame(REGISTRATIONS, index=YEARS, dtype="Int64")
GNI = pd.Series([4151, 4219, 4399, 4496], index=YEARS)
GNI_GROWTH = pd.Series([-0.3, 1.6, 4.3, 2.2], index=YEARS)
MARKET = pd.Series([1692145, 1759561, 1645998, 1695353], index=YEARS)
MARKET_NAME = "전국 자동차 신규등록"
GNI_NAME = "1인당 실질 국민총소득"
SELECTED_NAME = "선택 브랜드 신규등록"

SOURCES = {
    "KAIDA 2022년": "https://www.kaida.co.kr/ko/kaida/bbsView.do?articleNo=221&articleSeq=55280&bbsType=kaida&boardSeq=15&pageIndex=1&searchCondition=0&searchKeyword=",
    "KAIDA 2023년 발표 인용": "https://view.mk.co.kr/car-tech/article/47545/",
    "KAIDA 2024년 발표 인용": "https://www.globalepic.co.kr/view.php?ud=20250106120128296648439a4874_29",
    "KAIDA 2025년 발표 인용": "https://www.autoview.co.kr/ko-kr/articles/98637",
    "1인당 실질 국민총소득 · 국가지표체계": "https://www.index.go.kr/unity/potal/eNara/sub/showStblGams3.do?freq=Y&idx_cd=8086&period=N&stts_cd=422101",
    "전국 자동차 신규등록 · 국회예산정책처, 국토교통부": "https://www.nabo.go.kr/board/file/down.do?fid=33319731",
}


def layout(fig, height=330):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=22, t=45, b=12),
        legend=dict(orientation="h", y=1.03, yanchor="bottom"),
        hoverlabel=dict(namelength=-1),
    )
    return fig


def trend_chart(years, totals):
    fig = go.Figure()
    series = [
        (GNI_NAME, GNI, "만 원", "#E4A569"),
        (MARKET_NAME, MARKET, "대", "#A8ADB8"),
    ]
    if totals is not None:
        series.append((SELECTED_NAME, totals, "대", "#75AAD7"))

    for name, values, unit, color in series:
        visible = values.loc[years]
        fig.add_scatter(
            x=years, y=(100 * visible / visible.iloc[0]).tolist(), name=name,
            customdata=visible.tolist(), mode="lines+markers",
            line=dict(color=color, width=3), marker=dict(size=8),
            hovertemplate="%{x}년 · %{customdata:,.0f}" + unit + "<br>지수 %{y:.1f}<extra>%{fullData.name}</extra>",
        )

    fig.add_hline(y=100, line_dash="dot", line_color="#858C97", opacity=0.55)
    fig.update_xaxes(tickvals=years, ticksuffix="년")
    fig.update_yaxes(title=f"{years[0]}년 = 100")
    return layout(fig)


def scatter_chart(points, totals):
    fig = go.Figure()
    series = [(MARKET_NAME, MARKET, "#A8ADB8", "diamond")]
    if totals is not None:
        series.append((SELECTED_NAME, totals, "#75AAD7", "circle"))

    correlations = []
    for name, values, color, symbol in series:
        changes = (100 * values.pct_change()).loc[points]
        income = GNI_GROWTH.loc[points]
        fig.add_scatter(
            x=income.tolist(), y=changes.tolist(), name=name, mode="markers+text",
            customdata=points, text=[f"{year}년" for year in points],
            textposition="bottom right" if symbol == "diamond" else "top left",
            marker=dict(size=11, symbol=symbol, color=color),
            hovertemplate="%{customdata}년<br>소득 %{x:+.1f}%<br>등록 %{y:+.1f}%<extra>%{fullData.name}</extra>",
        )
        if len(points) >= 3 and changes.nunique() >= 2:
            correlations.append(f"{name} r = {income.corr(changes):+.2f}")

    if not points:
        fig.add_annotation(x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                           text="표시 기간에 전년 대비 비교가 가능한 연도가 없어요.")
    fig.update_xaxes(title="1인당 실질 GNI 증가율", ticksuffix="%", zeroline=True)
    fig.update_yaxes(title="신규등록 증가율", ticksuffix="%", zeroline=True)
    return layout(fig), correlations


def brand_chart(counts):
    available = counts.dropna().sort_values(ascending=False)
    fig = go.Figure()
    for group, color in GROUP_COLORS.items():
        brands = [brand for brand in available.index if BRAND_GROUP[brand] == group]
        if brands:
            registrations = available.loc[brands].astype(int).tolist()
            fig.add_bar(
                x=registrations, y=brands,
                orientation="h", name=group, marker_color=color,
                text=[f"{count:,}대" for count in registrations],
                textposition="outside", textangle=0, cliponaxis=False,
                hovertemplate="%{y} · %{x:,}대<extra>%{fullData.name}</extra>",
            )
    if available.empty:
        fig.add_annotation(x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                           text="선택한 연도에 확인된 등록대수가 없어요.")
    fig.update_xaxes(title="신규등록대수", tickformat=",d", ticksuffix="대", rangemode="tozero")
    if not available.empty:
        fig.update_xaxes(range=[0, max(1, int(available.max()) * 1.2)])
    fig.update_yaxes(categoryorder="array", categoryarray=available.index.tolist(), autorange="reversed")
    return layout(fig, max(235, 26 * len(available) + 86))


def group_change_chart(comparable, start, end):
    fig = go.Figure()
    groups = [group for group, brands in GROUPS.items() if any(brand in comparable for brand in brands)]
    if not groups or start == end:
        fig.add_annotation(
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            text="두 연도와 비교 가능한 브랜드를 선택하면 그룹별 변화가 표시돼요.",
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return layout(fig, 235)

    changes = COUNTS.loc[end, comparable] - COUNTS.loc[start, comparable]
    changes = [sum(changes[brand] for brand in comparable if BRAND_GROUP[brand] == group)
               for group in groups]
    fig.add_waterfall(
        x=[*groups, "전체 변화"], y=[*changes, sum(changes)],
        measure=["relative"] * len(groups) + ["total"],
        text=[f"{change:+,}대" for change in [*changes, sum(changes)]],
        textposition="outside", cliponaxis=False,
        connector=dict(line=dict(color="#818895", dash="dot")),
        increasing=dict(marker=dict(color="#78B5A4")),
        decreasing=dict(marker=dict(color="#E4A569")),
        totals=dict(marker=dict(color="#75AAD7")),
        hovertemplate="%{x}<br>%{text}<extra></extra>",
    )
    fig.update_yaxes(title="신규등록대수 변화", tickformat=",d", zeroline=True)
    return layout(fig, 300)


def main():
    st.set_page_config(page_title="소득과 고급 수입차", layout="wide")
    st.title("국민소득이 늘어난 해, 고급 수입차도 더 많이 등록됐을까?")
    st.caption("2022–2025년 전국 자동차 신규등록과 1인당 실질 국민총소득")

    start, end = st.sidebar.select_slider("비교 기간", options=YEARS, value=(2022, 2025),
                                          format_func=lambda year: f"{year}년")
    groups = st.sidebar.multiselect("브랜드 그룹", list(GROUPS), default=list(GROUPS))
    options = [brand for group in groups for brand in GROUPS[group]]
    brands = st.sidebar.multiselect(
        "브랜드 좁히기", options, placeholder="선택한 그룹의 모든 브랜드",
        help="비워 두면 선택한 그룹의 모든 브랜드를 표시해요.",
    )
    if not groups:
        st.info("사이드바에서 비교할 그룹을 선택해 주세요.")
        return

    brands = brands or options
    years = list(range(start, end + 1))
    selected = COUNTS[brands]
    comparable = selected.columns[selected.notna().all()].tolist()
    totals = selected[comparable].sum(axis=1).astype(float) if comparable else None
    latest = selected.loc[end]
    reported = latest.dropna()
    missing = latest[latest.isna()].index.tolist()

    income_card, market_card, brand_card = st.columns(3)
    income_card.metric(f"{end}년 1인당 실질 GNI", f"{GNI.at[end]:,}만 원", f"{GNI_GROWTH.at[end]:+.1f}% 전년 대비")
    market_card.metric(f"{end}년 전국 신규등록", f"{MARKET.at[end]:,}대")
    brand_card.metric(
        f"{end}년 선택 브랜드 · {len(reported)}/{len(brands)}개 확인",
        f"{int(reported.sum()):,}대" if len(reported) else "미확인",
    )
    excluded = [brand for brand in brands if brand not in comparable]
    if excluded:
        st.caption(
            "추세와 상관관계에는 4년치가 모두 확인된 브랜드만 집계했어요. "
            f"선택한 {len(brands)}개 중 {len(comparable)}개가 해당해요. "
            f"{', '.join(excluded)}의 확인된 수치는 브랜드별 차트와 데이터 표에서 볼 수 있어요."
        )

    config = {"displayModeBar": False}
    st.subheader("소득과 등록대수의 움직임")
    st.plotly_chart(trend_chart(years, totals), config=config, key="imports_trend")
    st.caption("선택한 첫해를 100으로 맞췄어요. 전국 수치는 승용·승합·화물·특수차를 포함하고, 브랜드별 수치는 수입 승용차 집계예요.")

    st.subheader("소득이 늘어난 해의 신규등록 증가율")
    points = [year for year in years if year > YEARS[0]]
    scatter, correlations = scatter_chart(points, totals)
    st.plotly_chart(scatter, config=config, key="imports_scatter")
    if correlations:
        st.caption("피어슨 상관계수 · " + " / ".join(correlations) + f" · 비교 연도 {len(points)}개")
    st.caption("각 점은 한 해의 전년 대비 증가율이에요. 브랜드 자료는 최대 3개 연도만 비교할 수 있어 상관계수는 참고용이에요.")

    st.subheader(f"{end}년 브랜드별 신규등록대수")
    st.plotly_chart(brand_chart(latest), config=config, key="imports_brands")
    if len(reported):
        share = 100 * reported.sum() / MARKET.at[end]
        st.caption(f"수치가 확인된 선택 브랜드가 전국 자동차 신규등록에서 차지한 비중은 {share:.2f}%예요.")
    if missing:
        st.caption(f"{end}년 연간 발표 수치 미확인 · {', '.join(missing)}")

    st.subheader(f"{start}년에서 {end}년까지, 어느 그룹이 얼마나 바뀌었을까?")
    st.plotly_chart(group_change_chart(comparable, start, end), config=config, key="imports_groups")
    st.caption("4년치가 확인된 선택 브랜드의 감소분과 증가분을 더하면 오른쪽 전체 변화가 돼요.")

    with st.expander("연도별 데이터와 출처"):
        table = selected.loc[years].T
        table.columns = [f"{year}년" for year in years]
        table.insert(0, "그룹", [BRAND_GROUP[brand] for brand in table.index])
        st.dataframe(table.astype("string").fillna("미확인"))
        st.caption("그룹 분류는 이 프로젝트의 기준이에요. 2025년 국민총소득은 잠정치예요.")
        st.markdown("\n".join(f"- [{label}]({url})" for label, url in SOURCES.items()))


main()
