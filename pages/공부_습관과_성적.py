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
PALETTE = ["#317972", "#b46742", "#6a699c", "#9b5069", "#687d41"]

raw = pd.read_csv(Path(__file__).with_name("study.csv"))
with st.sidebar:
    st.header("비교 조건")
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
a, b, c = st.columns(3)
a.metric("선택한 과목의 학생", f"{len(data)}명")
b.metric(f"{threshold} 받은 학생", f"{data['높은 성적'].sum()}명")
c.metric(f"{threshold} 비율", f"{data['높은 성적'].mean():.1%}")

st.markdown(
    "[UCI 원자료 및 코드북](https://archive.ics.uci.edu/dataset/856/higher+education+students+performance+evaluation)"
    " · Nevriye Yilmaz 및 Boran Şekeroğlu · CC BY 4.0"
)
if not questions:
    st.info("왼쪽에서 비교할 공부 습관을 하나 이상 선택하세요.")
    st.stop()

rows = []
for question in questions:
    column, labels = QUESTIONS[question]
    part = data[["높은 성적", "성적 등급"]].copy()
    part["공부 습관"] = question
    part["응답"] = data[column].map(labels)
    part["응답 항목"] = question + " · " + part["응답"]
    rows.append(part)
long = pd.concat(rows, ignore_index=True)
colors = dict(zip(QUESTIONS, PALETTE))
order = [f"{q} · {label}" for q in questions for label in QUESTIONS[q][1].values()]

st.subheader(f"1. 어떤 습관에서 {threshold} 비율이 높았을까?")
rates = long.groupby(["공부 습관", "응답 항목"], as_index=False).agg(
    응답자=("높은 성적", "size"), 고성적=("높은 성적", "sum")
)
rates["비율"] = rates["고성적"] / rates["응답자"] * 100
rates["표시"] = rates.apply(lambda r: f"{r['비율']:.1f}% (n={r['응답자']})", axis=1)
fig = px.bar(rates, x="비율", y="응답 항목", color="공부 습관", text="표시",
             color_discrete_map=colors, category_orders={"응답 항목": order},
             labels={"비율": f"{threshold} 비율 (%)", "응답 항목": ""},
             hover_data=["응답자", "고성적"])
fig.update_layout(height=110 + 35 * len(rates), showlegend=False, xaxis_range=[0, 100])
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, width="stretch")
st.caption("n은 해당 응답을 고른 학생 수입니다. 표본이 작을수록 한 명의 성적이 비율을 크게 바꿉니다.")

st.subheader("2. 각 공부 습관의 성적 분포는 어땠을까?")
dist = long.groupby(["응답 항목", "성적 등급"], as_index=False).size()
dist["비율"] = dist["size"] / dist.groupby("응답 항목")["size"].transform("sum") * 100
fig = px.bar(dist, x="비율", y="응답 항목", color="성적 등급", barmode="stack",
             category_orders={"응답 항목": order, "성적 등급": GRADES},
             color_discrete_sequence=["#a85545", "#ce8166", "#dfad91", "#e8cbb0",
                                      "#d8d9bf", "#9cbaaa", "#579387", "#2a6a63"],
             labels={"비율": "응답자 중 비율 (%)", "응답 항목": "", "size": "학생 수"},
             hover_data=["size"])
fig.update_layout(height=130 + 31 * len(rates), xaxis_range=[0, 100],
                  legend=dict(orientation="h", y=1.08))
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, width="stretch")

st.subheader(f"3. {threshold} 받은 학생은 어떻게 공부했을까?")
long["성적 집단"] = long["높은 성적"].map({True: "기준 충족", False: "기준 미충족"})
mix = long.groupby(["공부 습관", "성적 집단", "응답 항목"], as_index=False).size()
mix["비율"] = mix["size"] / mix.groupby(["공부 습관", "성적 집단"])["size"].transform("sum") * 100
grid = pd.MultiIndex.from_product(
    [rates["응답 항목"], mix["성적 집단"].unique()], names=["응답 항목", "성적 집단"]
).to_frame(index=False)
mix = grid.merge(mix[["응답 항목", "성적 집단", "비율", "size"]], how="left").fillna(0)
fig = px.bar(mix, x="비율", y="응답 항목", color="성적 집단", barmode="group",
             color_discrete_map={"기준 충족": "#317972", "기준 미충족": "#bd7959"},
             category_orders={"응답 항목": order, "성적 집단": ["기준 충족", "기준 미충족"]},
             labels={"비율": "각 성적 집단에서 해당 응답을 고른 비율 (%)",
                     "응답 항목": "", "size": "학생 수"}, hover_data=["size"])
fig.update_layout(height=130 + 39 * len(rates), xaxis_range=[0, 100],
                  legend=dict(orientation="h", y=1.08))
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, width="stretch")

st.caption("관찰 자료로 공부 습관과 성적의 관련성을 비교했습니다. 과목 난이도나 기존 학업 성취도의 영향을 포함할 수 있습니다.")
