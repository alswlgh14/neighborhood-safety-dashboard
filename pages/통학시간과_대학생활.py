import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="통학시간과 대학생활", layout="wide")

# Shin & Kim (2018), Tables 2–4. These values are published summaries.
COMMUTE = {
    "거주 형태": [("본가", 2322, 2.40), ("기숙사", 728, 1.48), ("자취·하숙", 442, 1.38)],
    "대학 소재지": [("수도권 대학", 1265, 2.29), ("지방 대학", 2324, 1.96)],
    "성별": [("남학생", 1712, 2.02), ("여학생", 1877, 2.13)],
}
VARIABLES = ["통학시간", "가구소득", "대학 몰입", "학업중단 의사"]
CORRELATIONS = pd.DataFrame(
    [[1.000, -.057, -.092, .089],
     [-.057, 1.000, .035, .026],
     [-.092, .035, 1.000, -.464],
     [.089, .026, -.464, 1.000]],
    columns=VARIABLES, index=VARIABLES,
)

with st.sidebar:
    st.header("비교 조건")
    group_by = st.selectbox("통학 비교 기준", list(COMMUTE))
    selected = st.multiselect(
        "비교할 집단", [group for group, _, _ in COMMUTE[group_by]],
        default=[group for group, _, _ in COMMUTE[group_by]],
        key=f"groups_{group_by}",
    )
    focal = st.selectbox("상관관계의 기준 변수", VARIABLES)

st.title("긴 통학, 대학생활과 어떤 관계가 있을까?")
st.caption("2011년 국내 대학생 조사 · 신혜숙·김미현(2018)의 논문 표 2~4")
st.write("어떤 집단이 더 오래 통학했는지, 통학시간이 대학 몰입과 학업중단 의사에 어떻게 관련됐는지 살펴봅니다.")

st.subheader("집단별 편도 통학 비교")
data = pd.DataFrame(COMMUTE[group_by], columns=["집단", "응답자 수", "통학 구간 평균"])
data = data[data["집단"].isin(selected)].sort_values("통학 구간 평균", ascending=False)
if data.empty:
    st.info("사이드바에서 비교할 집단을 하나 이상 선택하세요.")
else:
    size, gap = st.columns(2)
    size.metric("선택한 집단의 응답자 수", f"{data['응답자 수'].sum():,}명")
    spread = data["통학 구간 평균"].max() - data["통학 구간 평균"].min()
    gap.metric("선택 집단의 최대 차이", f"{spread:.2f}점" if len(data) > 1 else "집단 2개 필요")
    labels = data["통학 구간 평균"].map(lambda value: f"{value:.2f}")
    commute = px.scatter(data, x="통학 구간 평균", y="집단", text=labels,
                         hover_data={"응답자 수": ":,d", "통학 구간 평균": ":.2f"},
                         color_discrete_sequence=["#63b9ad"])
    commute.update_traces(marker_size=12, textposition="middle right")
    commute.update_xaxes(range=[0.85, 4.2], tickvals=[1, 2, 3, 4], fixedrange=True)
    commute.update_yaxes(title=None, autorange="reversed", fixedrange=True)
    commute.update_layout(height=100 + 47 * len(data), margin=dict(l=0, r=12, t=12, b=0))
    st.plotly_chart(commute, width="stretch", config={"displayModeBar": False})
st.caption("1 = 30분 미만 · 2 = 30분~1시간 미만 · 3 = 1~2시간 미만 · 4 = 2시간 이상. 숫자는 네 구간 코드의 평균입니다.")

left, right = st.columns(2)
with left:
    st.subheader(f"{focal}과 다른 변수의 상관관계")
    corr = CORRELATIONS[focal].drop(focal).rename_axis("변수").reset_index(name="상관계수")
    corr["방향"] = corr["상관계수"].map(lambda value: "양의 관계" if value >= 0 else "음의 관계")
    corr["표시"] = corr["상관계수"].map(lambda value: f"{value:+.3f}")
    bars = px.bar(corr, x="상관계수", y="변수", color="방향", text="표시",
                  orientation="h", color_discrete_map={"양의 관계": "#63b9ad", "음의 관계": "#e9a375"})
    bars.update_traces(textposition="outside", cliponaxis=False)
    bars.update_xaxes(range=[-.56, .56], zeroline=True, fixedrange=True)
    bars.update_yaxes(title=None, autorange="reversed", fixedrange=True)
    bars.update_layout(height=280, showlegend=False, margin=dict(l=0, r=12, t=12, b=0))
    st.plotly_chart(bars, width="stretch", config={"displayModeBar": False})
    st.caption("막대의 방향은 관계의 방향을, 길이는 관계의 강도를 보여줍니다.")

with right:
    st.subheader("통학시간과 학업중단 의사의 경로")
    model = go.Figure()
    for x0, y0, x1, y1 in [(.28, .2, .83, .2), (.26, .28, .51, .69), (.63, .69, .86, .28)]:
        model.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
            arrowhead=2, arrowsize=1, arrowwidth=1.8, arrowcolor="#8794a3"
        )
    for x, y, label in [
        (.18, .2, "통학시간"), (.57, .79, "대학 몰입"), (.89, .13, "학업중단 의사"),
        (.40, .51, "−0.112"), (.76, .51, "−0.462"), (.55, .25, "+0.049"),
    ]:
        model.add_annotation(x=x, y=y, text=label, showarrow=False, font_size=13)
    model.update_xaxes(visible=False, range=[0, 1.04], fixedrange=True)
    model.update_yaxes(visible=False, range=[0, 1], fixedrange=True)
    model.update_layout(height=280, margin=dict(l=10, r=10, t=12, b=0))
    st.plotly_chart(model, width="stretch", config={"displayModeBar": False})
    st.caption("논문의 전체 표본 모형에 보고된 표준화 경로계수입니다. 왼쪽 필터로 다시 추정하지 않습니다.")

st.caption("학업중단 의사는 자퇴·휴학(군입대 제외)·학교를 옮길 의향을 묻는 지표입니다. 이 화면은 관찰된 관계를 보여줍니다.")
st.markdown("[논문과 원자료 출처](https://doi.org/10.22327/kei.2018.36.1.025) · 한국교육종단연구2005, 2011년 7차")
