import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# KTDB reports, 2023 Table 4-6 and 2025 Table 4-10.
SURVEY_COUNTS = {
    2021: (2436, 257, 856, 156, 4653, 3592),
    2022: (2880, 395, 1502, 204, 2522, 2358),
    2023: (3135, 553, 1811, 178, 2566, 2224),
    2024: (2734, 464, 1834, 167, 2279, 2192),
    2025: (2309, 971, 2391, 134, 1830, 2276),
}
# MOLIT registration workbooks, sheet 01.통계표, nationwide September totals.
REGISTERED = {
    2021: 24_778_004,
    2022: 25_355_938,
    2023: 25_845_648,
    2024: 26_202_541,
    2025: 26_456_457,
    2026: 26_706_123,
}
# Published actual daily averages during the special traffic management periods.
HIGHWAY = {
    2021: (479, "9.17–9.22", 6),
    2022: (553, "9.8–9.12", 5),
    2023: (554, "9.27–10.3", 7),
    2024: (555, "9.13–9.18", 6),
    2025: (541, "10.2–10.12", 11),
    2026: (609, "9.23–9.27", 5),
}
# September 2026 traffic management plan, Appendix 1, Figure 3.
PUBLISHED_2026 = (49.5, 15.1, 17.6, 17.8)
CATEGORIES = ("귀성만", "귀성과 여행", "여행만", "이동 계획 없음", "미정")
COLORS = ("#EDAB66", "#B77946", "#72A9DD", "#A5ADB9", "#B49ECC")
BLUE = "#72A9DD"
ORANGE = "#EDAB66"


def survey_data(years, exclude_undecided):
    rows = {}
    sizes = {}
    for year in years:
        if year == 2026:
            if exclude_undecided:
                rows[year] = PUBLISHED_2026
                sizes[year] = "산출 분모 미공개"
            continue

        home, both, travel, reverse, no_plan, undecided = SURVEY_COUNTS[year]
        counts = (home, both, travel, reverse + no_plan, undecided)
        if exclude_undecided:
            counts = counts[:-1]
        denominator = sum(counts)
        rows[year] = tuple(100 * count / denominator for count in counts)
        sizes[year] = f"{denominator:,}가구"

    category_count = 4 if exclude_undecided else 5
    survey = pd.DataFrame.from_dict(rows, orient="index", columns=CATEGORIES[:category_count])
    survey["귀성 계획"] = survey["귀성만"] + survey["귀성과 여행"]
    survey["분모"] = pd.Series(sizes, dtype="object")
    return survey


def format_chart(fig, height):
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=20, t=35, b=12),
        hoverlabel=dict(namelength=-1),
        font=dict(size=13),
    )
    return fig


def trend_chart(years, survey):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.16,
        subplot_titles=("자동차 누적 등록대수", "귀성 계획 비율"),
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=[REGISTERED[year] / 10_000 for year in years],
            customdata=[REGISTERED[year] for year in years],
            mode="lines+markers", line=dict(color=BLUE, width=3), marker=dict(size=8),
            hovertemplate="%{x}년 9월 말 · %{customdata:,.0f}대<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=survey.index.tolist(), y=survey["귀성 계획"].tolist(),
            customdata=survey["분모"].tolist(), mode="lines+markers",
            line=dict(color=ORANGE, width=3), marker=dict(size=8),
            hovertemplate="%{x}년 · %{y:.1f}%<br>%{customdata}<extra></extra>",
        ),
        row=2, col=1,
    )
    if survey.empty:
        fig.add_annotation(text="선택한 기준으로 공개된 값이 없어요", xref="x2 domain",
                           yref="y2 domain", x=0.5, y=0.55, showarrow=False)
    fig.update_yaxes(title_text="만 대", tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(title_text="비율", ticksuffix="%", range=[0, 100], row=2, col=1)
    fig.update_xaxes(tickvals=years, ticksuffix="년", range=[min(years) - 0.4, max(years) + 0.4])
    fig.update_layout(showlegend=False)
    return format_chart(fig, 395)


def composition_chart(years, survey, exclude_undecided):
    fig = go.Figure()
    category_count = 4 if exclude_undecided else 5
    plot_years = [f"{year}년" for year in years]
    for name, color in zip(CATEGORIES[:category_count], COLORS):
        percentages = survey[name].reindex(years).tolist()
        labels = [f"{value:.0f}%" if value >= 11 else "" for value in percentages]
        fig.add_bar(
            x=percentages, y=plot_years, orientation="h", name=name, marker_color=color,
            text=labels, textposition="inside", insidetextanchor="middle",
            insidetextfont=dict(color="#191C24"),
            hovertemplate="%{y} · %{fullData.name} %{x:.1f}%<extra></extra>",
        )
    if survey.empty:
        fig.add_annotation(text="2026년 미정 포함 응답 구성 미공개", x=50, y=plot_years[0],
                           showarrow=False)
    elif 2026 in years and 2026 not in survey.index:
        fig.add_annotation(text="미정 포함 수치 미공개", x=50, y="2026년", showarrow=False)
    fig.update_layout(
        barmode="stack", bargap=0.32,
        legend=dict(orientation="h", y=1.03, yanchor="bottom"),
    )
    fig.update_xaxes(range=[0, 100], ticksuffix="%", dtick=25)
    fig.update_yaxes(categoryorder="array", categoryarray=plot_years, autorange="reversed")
    return format_chart(fig, max(275, 53 * len(years) + 85))


def traffic_chart(years):
    traffic = [HIGHWAY[year][0] for year in years]
    dates = [f"{HIGHWAY[year][1]} · {HIGHWAY[year][2]}일" for year in years]
    fig = go.Figure(go.Scatter(
        x=years, y=traffic, customdata=dates, mode="markers+text",
        marker=dict(size=14, color="#81B7A4"),
        text=[f"{value}만" for value in traffic], textposition="top center",
        hovertemplate="%{x}년 · 하루 %{y}만 대<br>%{customdata}<extra></extra>",
    ))
    fig.update_xaxes(tickvals=years, ticksuffix="년",
                     range=[min(years) - 0.55, max(years) + 0.55])
    fig.update_yaxes(title_text="만 대/일", range=[420, 665], dtick=50)
    return format_chart(fig, 300)


def main():
    st.set_page_config(page_title="자동차와 추석 귀성", layout="wide")
    st.title("차는 늘었는데, 추석에 고향 갈 계획을 세운 가구도 늘었을까?")
    st.caption("2021–2026년 전국 자동차 등록 통계와 한국교통연구원 추석 사전조사")

    options = list(REGISTERED)
    years = sorted(st.sidebar.multiselect("비교 연도", options, default=options,
                                          format_func=lambda year: f"{year}년"))
    basis = st.sidebar.radio("귀성 설문 집계 기준", ("미정 제외", "미정 포함"))
    exclude_undecided = basis == "미정 제외"
    st.sidebar.caption("2026년 귀성 설문은 미정 제외 비율만 공개됐어요.")
    if not years:
        st.info("비교 연도를 하나 이상 선택해 주세요.")
        return

    survey = survey_data(years, exclude_undecided)
    first, last = years[0], years[-1]
    car_change = 100 * (REGISTERED[last] / REGISTERED[first] - 1)
    car_delta = f"{first}년 대비 {car_change:+.1f}%" if first != last else None
    cars, plans, highway = st.columns(3)
    cars.metric(f"{last}년 9월 말 등록대수", f"{REGISTERED[last] / 10_000:,.1f}만 대",
                car_delta)
    if survey.empty:
        plans.metric(f"{last}년 귀성 계획 · {basis}", "미공개")
    else:
        survey_first, survey_last = survey.index[0], survey.index[-1]
        rate = survey.at[survey_last, "귀성 계획"]
        change = rate - survey.at[survey_first, "귀성 계획"]
        plan_delta = f"{survey_first}년 대비 {change:+.1f}%p" if len(survey) > 1 else None
        plans.metric(f"{survey_last}년 귀성 계획 · {basis}", f"{rate:.1f}%", plan_delta)
    highway.metric(f"{last}년 추석 하루 평균 통행", f"{HIGHWAY[last][0]}만 대")

    config = {"displayModeBar": False}
    st.subheader("자동차 등록과 귀성 계획의 변화")
    st.plotly_chart(trend_chart(years, survey), config=config)
    st.caption("귀성 비율은 ‘귀성만’과 ‘귀성과 여행’ 응답을 합한 값이에요. 연도별 전국 집계로 차량 등록과 귀성 결정의 인과관계를 판단하기는 어려워요.")

    st.subheader("응답은 어떻게 나뉘었을까?")
    st.plotly_chart(composition_chart(years, survey, exclude_undecided), config=config)
    st.caption("본인이 이동할 계획이 없는 역귀성 응답은 ‘이동 계획 없음’에 넣었어요.")

    st.subheader("추석 고속도로의 하루 평균 통행량")
    st.plotly_chart(traffic_chart(years), config=config)
    st.caption("각 해 특별교통대책기간의 실제 차량 통행 집계예요. 여행, 귀경 등 여러 목적의 통행이 함께 포함돼요.")

    with st.expander("데이터 출처와 집계 기준"):
        st.markdown(
            "- [국토교통부 자동차등록현황보고](https://stat.molit.go.kr/portal/cate/statMetaView.do?hFormId=5498&hRsId=58) · 각 연도 9월 파일의 ‘01.통계표’ 전국 합계\n"
            "- [한국교통연구원 2023년 표 4-6](https://www.ktdb.go.kr/DATA/pblcte/20250123015616835.pdf#page=147) · 2021–2023년 응답 가구 수\n"
            "- [한국교통연구원 2025년 표 4-10](https://www.ktdb.go.kr/DATA/pblcte/20260512020104063.pdf#page=268) · 2024–2025년 응답 가구 수\n"
            "- [국토교통부 2026년 추석 특별교통대책 첨부자료](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156782516) · 참고 1 그림 3, 미정 제외 공개 비율\n"
            "- 추석 고속도로 실적 · [2021년](https://www.korea.kr/news/policyNewsView.do?newsId=148893496) · [2022년](https://www.korea.kr/news/policyNewsView.do?newsId=148905860) · [2023–2024년](https://itskorea.kr/downloadFile.do?fileId=FILE_000000000087675&fileSn=0) · [2025년](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156782516) · [2026년](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156783487)"
        )
        st.caption("2026년 귀성 설문은 공개 비율을 사용했어요. 조사 전체 표본은 10,024명이지만 미정 응답을 제외한 집계 분모와 항목별 빈도는 첨부자료에 공개되지 않았어요.")
        st.caption("2026년 첨부자료에 함께 실린 2025년 값은 사후 회고 응답이에요. 이 화면의 2025년 값은 그해 사전조사에서 가져왔어요.")


main()
