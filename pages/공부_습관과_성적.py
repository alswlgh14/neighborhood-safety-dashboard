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
GRADES = ["Fail", "DD", "DC", "CC", "CB", "BB", "BA", "AA"]

raw = pd.read_csv(Path(__file__).with_name("study.csv"))
with st.sidebar:
    st.header("비교 조건")
    st.caption("여기서 고른 습관이 본문 버튼에 표시됩니다.")
    questions = st.multiselect("비교할 공부 습관", list(QUESTIONS), default=list(QUESTIONS)[:3])
    courses = st.multiselect("과목 코드 (비워두면 전체)", sorted(raw.course_id.unique()))
    threshold = st.selectbox("높은 성적의 기준", ["AA만", "BA 이상", "BB 이상"], index=1)

cutoff = {"AA만": 7, "BA 이상": 6, "BB 이상": 5}[threshold]
data = raw[raw.course_id.isin(courses)].copy() if courses else raw.copy()
data["높은 성적"] = data.grade.ge(cutoff)
data["성적 등급"] = data.grade.map(dict(enumerate(GRADES)))

st.title("벼락치기 vs 꾸준히 공부")
st.write("공부 습관이 다른 학생들은 과목 성적도 달랐을까?")
st.caption("2019년 대학생 설문과 과목 성적 · UCI 공개 데이터")
if not questions:
    st.info("왼쪽에서 비교할 공부 습관을 하나 이상 선택하세요.")
    st.stop()

question = st.radio("살펴볼 공부 습관", questions, horizontal=True)
column, labels = QUESTIONS[question]
data["응답"] = data[column].map(labels)
order = [label for label in labels.values() if label in data["응답"].values]

rates = data.groupby("응답", as_index=False).agg(
    학생=("높은 성적", "size"), 고성적=("높은 성적", "sum")
)
rates["비율"] = rates["고성적"] / rates["학생"] * 100
rates["표시"] = rates.apply(
    lambda r: f"{r['비율']:.1f}% · {r['고성적']}/{r['학생']}명", axis=1
)

st.caption(f"선택한 과목의 학생 {len(data)}명 · {threshold} {data['높은 성적'].sum()}명")
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
fig.update_layout(height=125 + 42 * len(order), margin=dict(l=0, r=116, t=8, b=0), xaxis_range=[0, 100])
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, width="stretch")
st.caption("막대 옆 숫자는 기준을 충족한 학생 수 / 해당 응답을 고른 학생 수입니다.")

left, right = st.columns(2)
with left:
    st.subheader("전체 성적 분포")
    st.caption("같은 등급에서 점이 높을수록 그 등급을 받은 학생의 비율이 높습니다.")
    counts = pd.crosstab(data["응답"], data["성적 등급"]).reindex(
        index=order, columns=GRADES, fill_value=0
    )
    totals = counts.sum(axis=1)
    dist = counts.stack().rename("학생 수").reset_index()
    dist["응답자 수"] = dist["응답"].map(totals)
    dist["비율"] = dist["학생 수"] / dist["응답자 수"] * 100
    dist["응답 그룹"] = dist["응답"] + " (" + dist["응답자 수"].astype(str) + "명)"
    groups = [f"{label} ({totals[label]}명)" for label in order]
    # Slight offsets leave room for equal rates within a grade.
    offsets = {label: (i - (len(order) - 1) / 2) * 0.14 for i, label in enumerate(order)}
    dist["등급 위치"] = dist["성적 등급"].map(dict(zip(GRADES, range(len(GRADES)))))
    dist["등급 위치"] += dist["응답"].map(offsets)
    chart = px.scatter(
        dist, x="등급 위치", y="비율", color="응답 그룹", symbol="응답 그룹",
        category_orders={"응답 그룹": groups},
        color_discrete_sequence=["#65bcb1", "#e7a46e", "#9c9bdb", "#cc84a2", "#adc57d"],
        symbol_sequence=["circle", "diamond", "square", "triangle-up", "cross"],
        custom_data=["응답", "성적 등급", "학생 수", "응답자 수"],
    )
    chart.update_traces(
        marker=dict(size=9, opacity=1),
        hovertemplate="%{customdata[0]} · %{customdata[1]}<br>"
                      "%{y:.1f}% (%{customdata[2]}/%{customdata[3]}명)<extra></extra>",
    )
    chart.update_xaxes(title=None, tickmode="array", tickvals=list(range(len(GRADES))),
                       ticktext=GRADES, range=[-0.55, len(GRADES) - 0.45], showgrid=False)
    chart.update_yaxes(title="학생 비율", ticksuffix="%", rangemode="tozero")
    chart.update_layout(height=350, margin=dict(l=0, r=8, t=50, b=0),
                        legend=dict(orientation="h", y=1, yanchor="bottom", title=None))
    st.plotly_chart(chart, width="stretch")

with right:
    st.subheader("성적 집단별 공부 습관")
    data["성적 집단"] = data["높은 성적"].map({True: "기준 충족", False: "기준 미충족"})
    mix = pd.crosstab(data["응답"], data["성적 집단"]).stack().rename("학생 수").reset_index()
    mix["비율"] = mix["학생 수"] / mix.groupby("성적 집단")["학생 수"].transform("sum") * 100
    chart = px.bar(
        mix, x="비율", y="응답", color="성적 집단", barmode="group",
        color_discrete_map={"기준 충족": "#317972", "기준 미충족": "#bd7959"},
        category_orders={"응답": order, "성적 집단": ["기준 충족", "기준 미충족"]},
        labels={"비율": "각 성적 집단에서 응답한 비율 (%)", "응답": ""},
        hover_data={"학생 수": True, "비율": ":.1f"},
    )
    chart.update_yaxes(autorange="reversed")
    chart.update_layout(height=335, xaxis_range=[0, 100], margin=dict(l=0, r=8, t=55, b=0),
                        legend=dict(orientation="h", y=1.04, title=None))
    st.plotly_chart(chart, width="stretch")

st.caption("응답자가 적은 항목은 한 명의 성적이 비율을 크게 바꿀 수 있습니다. 설문과 성적에서 관찰된 차이에는 과목 난이도 등 다른 요인도 영향을 줄 수 있습니다.")
st.markdown(
    "[UCI 원자료 및 코드북](https://archive.ics.uci.edu/dataset/856/higher+education+students+performance+evaluation)"
    " · Nevriye Yilmaz 및 Boran Şekeroğlu · CC BY 4.0"
)
