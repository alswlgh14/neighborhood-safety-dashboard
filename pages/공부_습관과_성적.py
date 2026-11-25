from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="벼락치기 vs 꾸준히 공부", layout="wide")

QUESTIONS = {
    "시험 준비 시점": ("prep_when", {1: "시험 직전에", 2: "학기 중 꾸준히", 3: "준비하지 않음"}),
    "혼공 vs 친구와 공부": ("prep_with", {1: "혼자 공부", 2: "친구와 공부", 3: "해당 없음"}),
    "수업 필기": ("notes", {1: "하지 않음", 2: "가끔", 3: "항상"}),
    "출석": ("attendance", {1: "항상", 2: "가끔", 3: "하지 않음"}),
    "주당 공부 시간": ("study_hours", {1: "없음", 2: "5시간 미만", 3: "6~10시간",
                                        4: "11~20시간", 5: "20시간 초과"}),
}

raw = pd.read_csv(Path(__file__).with_name("study.csv"))
with st.sidebar:
    st.header("비교 조건")
    st.caption("여기서 고른 습관이 본문 버튼에 표시됩니다.")
    questions = st.multiselect("비교할 공부 습관", list(QUESTIONS), default=list(QUESTIONS)[:3])
    courses = st.multiselect("과목 코드 (비워두면 전체)", sorted(raw.course_id.unique()))
    threshold = st.selectbox("높은 성적의 기준", ["A+만", "B+ 이상", "B 이상"], index=1)

cutoff = {"A+만": 7, "B+ 이상": 6, "B 이상": 5}[threshold]
data = raw[raw.course_id.isin(courses)].copy() if courses else raw.copy()
data["높은 성적"] = data.grade.ge(cutoff)

st.title("벼락치기 vs 꾸준히 공부")
st.write("공부 습관이 다른 학생들은 과목 성적도 달랐을까?")
st.caption("2019년 대학생 설문과 과목 성적 · UCI 공개 데이터")
if not questions:
    st.info("왼쪽에서 비교할 공부 습관을 하나 이상 선택하세요.")
    st.stop()

question = st.radio("살펴볼 공부 습관", questions, horizontal=True)
column, labels = QUESTIONS[question]
excluded = 0
if column in ("prep_when", "prep_with"):
    excluded = int((~data[column].isin([1, 2])).sum())
    data = data[data[column].isin([1, 2])].copy()
    if data.empty:
        st.info("선택한 과목에 비교할 시험 준비 응답이 없습니다.")
        st.stop()

data["응답"] = data[column].map(labels)
order = [label for label in labels.values() if label in data["응답"].values]

rates = data.groupby("응답", as_index=False).agg(
    학생=("높은 성적", "size"), 고성적=("높은 성적", "sum")
)
rates["비율"] = rates["고성적"] / rates["학생"] * 100
rates["표시"] = rates.apply(
    lambda r: f"{r['비율']:.1f}% · {r['고성적']}/{r['학생']}명", axis=1
)

sample, result = st.columns(2)
sample.metric("분석 대상 학생 수", f"{len(data)}명")
result.metric(f"{threshold} 비율", f"{data['높은 성적'].mean():.1%}",
              help=f"{data['높은 성적'].sum()}명 / {len(data)}명")
st.subheader(f"{question}에 따라 {threshold} 비율은?")
summary = rates.set_index("응답")
if question == "시험 준비 시점" and all(
    label in summary.index for label in ("학기 중 꾸준히", "시험 직전에")
):
    steady = summary.loc["학기 중 꾸준히", "비율"]
    last_minute = summary.loc["시험 직전에", "비율"]
    st.markdown(f"학기 중 꾸준히 **{steady:.1f}%** · 시험 직전에 **{last_minute:.1f}%**")
fig = px.bar(
    rates, x="비율", y="응답", text="표시", orientation="h",
    category_orders={"응답": order}, color_discrete_sequence=["#317972"],
    labels={"비율": f"{threshold} 비율 (%)", "응답": ""},
)
fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>%{text}<extra></extra>")
# Start at zero and leave room for the value labels near the longest bar.
axis_max = min(100, max(30, (int(rates["비율"].max() / 10) + 1) * 10))
fig.update_layout(height=125 + 42 * len(order), margin=dict(l=8, r=100, t=8, b=8),
                  dragmode=False)
fig.update_xaxes(range=[0, axis_max], fixedrange=True, automargin=True)
fig.update_yaxes(autorange="reversed", fixedrange=True, automargin=True)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
if question == "시험 준비 시점":
    st.caption("시험 직전에 또는 학기 중 꾸준히 준비했다고 응답한 학생을 비교합니다.")
elif column == "prep_with" and excluded:
    st.caption(f"공부 방식 비교에서 ‘해당 없음’ 응답 {excluded}명을 제외했습니다.")
st.caption("막대 옆 숫자는 기준을 충족한 학생 수 / 해당 응답을 고른 학생 수입니다.")

left, right = st.columns(2)
with left:
    st.subheader("공부 습관별 성적 분포")
    bands = ["D 이하", "C·C+·B", "B+·A+"]
    grade_bands = dict(zip(range(8), [bands[0]] * 3 + [bands[1]] * 3 + [bands[2]] * 2))
    distribution = data.assign(성적구간=data.grade.map(grade_bands))
    counts = pd.crosstab(distribution["응답"], distribution["성적구간"]).reindex(
        index=order, columns=bands, fill_value=0
    )
    totals = counts.sum(axis=1)
    dist = counts.stack().rename("학생 수").reset_index()
    dist["응답자 수"] = dist["응답"].map(totals)
    dist["비율"] = dist["학생 수"] / dist["응답자 수"] * 100
    dist["표시"] = dist["비율"].map(lambda rate: f"{rate:.0f}%" if rate >= 12 else "")
    dist["응답 그룹"] = dist["응답"] + " (" + dist["응답자 수"].astype(str) + "명)"
    groups = [f"{label} ({totals[label]}명)" for label in order]
    chart = px.bar(
        dist, x="비율", y="응답 그룹", color="성적구간", text="표시",
        orientation="h", barmode="stack",
        category_orders={"성적구간": bands, "응답 그룹": groups},
        color_discrete_map={"D 이하": "#d8977e", "C·C+·B": "#c6cad4", "B+·A+": "#65bcb1"},
        custom_data=["성적구간", "학생 수", "응답자 수"],
        labels={"응답 그룹": "", "비율": "학생 비율 (%)"},
    )
    chart.update_traces(
        textposition="inside", insidetextanchor="middle", textfont_color="#172127",
        hovertemplate="%{y} · %{customdata[0]}<br>"
                      "%{x:.1f}% (%{customdata[1]}/%{customdata[2]}명)<extra></extra>",
    )
    chart.update_xaxes(range=[0, 100], dtick=25, ticksuffix="%")
    chart.update_yaxes(autorange="reversed")
    chart.update_layout(height=325, margin=dict(l=0, r=8, t=36, b=0),
                        legend=dict(orientation="h", y=1.02, yanchor="bottom", title=None))
    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})


with right:
    st.subheader("성적 집단별 공부 습관")
    above, below = threshold, {"A+만": "A+ 미만", "B+ 이상": "B+ 미만", "B 이상": "B 미만"}[threshold]
    data["성적 집단"] = data["높은 성적"].map({True: above, False: below})
    counts = pd.crosstab(data["응답"], data["성적 집단"]).reindex(order)
    totals = counts.sum(axis=0)
    rates_by_grade = counts.div(totals, axis="columns") * 100
    mix = counts.stack().rename("학생 수").reset_index()
    mix["집단 인원"] = mix["성적 집단"].map(totals)
    mix["비율"] = mix["학생 수"] / mix["집단 인원"] * 100
    mix["표시"] = mix["비율"].map(lambda rate: f"{rate:.1f}%")
    rows = dict(zip(order, range(len(order))))
    mix["행"] = mix["응답"].map(rows)
    chart = px.scatter(
        mix, x="비율", y="행", color="성적 집단", symbol="성적 집단", text="표시",
        color_discrete_map={above: "#63b9ad", below: "#e9a375"},
        symbol_map={above: "circle", below: "diamond-open"},
        category_orders={"성적 집단": [above, below]},
        custom_data=["응답", "학생 수", "집단 인원"],
    )
    if above in totals and below in totals:
        for response, row in rows.items():
            chart.add_shape(
                type="line", x0=rates_by_grade.at[response, above],
                x1=rates_by_grade.at[response, below], y0=row, y1=row,
                line=dict(color="#8794a3", width=2), layer="below",
            )
    chart.update_traces(
        marker_size=9,
        hovertemplate="%{customdata[0]} · %{x:.1f}%<br>"
                      "%{customdata[1]}/%{customdata[2]}명",
    )
    chart.update_traces(selector=dict(name=above), textposition="top center")
    chart.update_traces(selector=dict(name=below), textposition="bottom center")
    chart.update_yaxes(title=None, tickvals=list(rows.values()), ticktext=order,
                       range=[len(order) - 0.5, -0.5], showgrid=False)
    chart.update_xaxes(title="각 성적 집단에서 응답한 비율", range=[-5, 105],
                       tickvals=[0, 25, 50, 75, 100], ticksuffix="%")
    chart.update_layout(height=max(325, 100 + 52 * len(order)),
                        margin=dict(l=0, r=12, t=36, b=0),
                        legend=dict(orientation="h", y=1.02, yanchor="bottom", title=None))
    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    if len(totals) == 1:
        st.caption("선택한 조건에서는 성적 집단 하나만 표시됩니다.")

st.caption("응답자가 적은 항목은 한 명의 성적이 비율을 크게 바꿀 수 있습니다. 설문과 성적에서 관찰된 차이에는 과목 난이도 등 다른 요인도 영향을 줄 수 있습니다.")
with st.expander("성적 표기 기준"):
    st.write("원자료 등급을 대시보드에서 읽기 쉬운 이름으로 표시했습니다.")
    st.caption("AA → A+, BA → B+, BB → B, CB → C+, CC → C")
    st.caption("‘D 이하’에는 원자료의 DC, DD, Fail을 포함합니다. 원자료의 낙제 등급은 Fail입니다.")
    st.caption("‘B+ 이상’은 원자료의 AA와 BA입니다. 평점 환산 없이 기존 등급 코드로 계산합니다.")
st.markdown(
    "[UCI 원자료 및 코드북](https://archive.ics.uci.edu/dataset/856/higher+education+students+performance+evaluation)"
    " · Nevriye Yilmaz 및 Boran Şekeroğlu · CC BY 4.0"
)
