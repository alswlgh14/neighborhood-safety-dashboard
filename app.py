from pathlib import Path
import plotly.express as px
import pandas as pd
import streamlit as st

st.set_page_config(page_title="동네의 모습과 밤의 두려움", layout="wide")
ITEMS = ["쓰레기와 지저분함", "어둡고 후미진 곳", "방치된 차와 빈 건물", "기초 질서 위반", "무리 지어 다니는 불량 청소년", "큰소리로 다투는 사람"]
FEAR = ["전혀 그렇지 않다", "그렇지 않은 편", "보통", "그런 편", "매우 그렇다"]
COLORS = ["#627f90", "#a3b8be", "#e6dfd2", "#e2ad79", "#b65740"]
raw = pd.read_csv(Path(__file__).with_name("counts.csv"))
st.caption("동네의 모습과 밤의 두려움  /  2016 개인 설문과 2024 지역 통계")
st.title("내가 사는 동네, 밤에도 안심할 수 있을까?")
st.write("동네 환경을 어떻게 느끼는지에 따라 혼자 있을 때의 두려움이 달라지는지 살펴봅니다.")
st.header("1. 동네 환경과 밤길 두려움 · 2016년")
st.caption("아래는 개인의 설문 응답을 분석한 결과입니다. 2024년 지역 통계와 직접 연결하지 않습니다.")
a,b = st.columns(2)
item = a.selectbox("동네 환경", ITEMS)
fear = b.radio("두려움을 느끼는 상황", ["밤에 혼자 골목길을 걸을 때", "밤에 혼자 집에 있을 때"], horizontal=True)
ftype = 2 if "골목길" in fear else 1
data = raw[raw.fear_type.eq(ftype)].copy()
data["환경"] = data.item.map(dict(enumerate(ITEMS, 1)))
data["환경 응답"] = data.environment.map({1:"동의하지 않음",2:"동의하지 않음",3:"보통",4:"동의함",5:"동의함"})
data["두려움 응답"] = data.fear.map(dict(enumerate(FEAR, 1)))
data["두려움"] = data["count"].where(data.fear.ge(4), 0)
selected = data[data.item.eq(ITEMS.index(item)+1)]
tot = int(selected["count"].sum())
agree = selected[selected.environment.ge(4)]
disagree = selected[selected.environment.le(2)]
def rate(frame):
    return frame["두려움"].sum()/frame["count"].sum()
m1,m2,m3=st.columns(3)
m1.metric("분석 응답자", f"{tot:,}명")
m2.metric("동네 환경에 동의한 집단의 두려움", f"{rate(agree):.1%}")
m3.metric("동의하지 않은 집단의 두려움", f"{rate(disagree):.1%}")
st.caption("두려움은 선택한 상황에서 ‘그런 편’과 ‘매우 그렇다’고 응답한 비율입니다.")

left, right = st.columns(2)
with left:
    st.subheader("어떤 동네 환경을 느꼈을까?")
    grouped = data.groupby(["환경", "environment"], as_index=False)["count"].sum()
    grouped["positive"] = grouped["count"].where(grouped.environment.ge(4), 0)
    grouped = grouped.groupby("환경", as_index=False)[["count", "positive"]].sum()
    grouped["비율"] = grouped.positive / grouped["count"] * 100
    fig1 = px.bar(grouped, x="비율", y="환경", orientation="h", text_auto=".1f",
                  labels={"비율":"동의한 응답자 비율 (%)", "환경":""}, color_discrete_sequence=["#75919a"],
                  category_orders={"환경":ITEMS[::-1]})
    st.plotly_chart(fig1, width="stretch")
with right:
    st.subheader("환경 인식별 두려움 응답 분포")
    dist = selected.groupby(["환경 응답","두려움 응답","fear"], as_index=False)["count"].sum()
    dist["total"] = dist.groupby("환경 응답")["count"].transform("sum")
    dist["비율"] = dist["count"] / dist.total * 100
    fig2 = px.bar(dist, x="환경 응답", y="비율", color="두려움 응답",
                  category_orders={"환경 응답":["동의하지 않음","보통","동의함"], "두려움 응답":FEAR},
                  color_discrete_sequence=COLORS,
                  labels={"환경 응답":item+" 인식", "비율":"응답자 비율 (%)", "두려움 응답":"두려움 정도"},
                  hover_data={"count":True,"비율":":.1f"})
    fig2.update_layout(barmode="stack", legend=dict(orientation="h",y=-0.3))
    st.plotly_chart(fig2, width="stretch")
st.subheader("동네 환경별 두 집단의 두려움 비교")
st.caption("각 동네 환경에 동의한 집단과 동의하지 않은 집단을 비교합니다.")
comparison = data[data.environment.isin([1,2,4,5])].groupby(["환경","환경 응답"],as_index=False)[["count","두려움"]].sum()
comparison["비율"] = comparison["두려움"] / comparison["count"] * 100
fig3 = px.bar(comparison, x="환경", y="비율", color="환경 응답", barmode="group", text_auto=".1f",
              category_orders={"환경":ITEMS,"환경 응답":["동의하지 않음","동의함"]},
              color_discrete_map={"동의하지 않음":"#75919a","동의함":"#b65740"},
              labels={"환경":"동네 환경","비율":"두렵다고 답한 비율 (%)","환경 응답":"환경 인식"},
              hover_data={"count":True})
fig3.update_layout(legend=dict(orientation="h",y=1.14))
st.plotly_chart(fig3, width="stretch")
st.caption("2016년 조사 응답자의 주관적인 환경 인식과 두려움입니다. 비율은 표본 가중치를 적용하지 않았으며 인과관계를 뜻하지 않습니다. 동네 환경에 동의한 비율은 두려움 상황 선택과 관계없이 동일합니다.")
st.markdown("[자료 출처: 한국형사·법무정책연구원, 전국범죄피해조사 2016](https://www.kicj.re.kr/board.es?act=view&bid=0062&list_no=14757&mid=a10905000000)")


st.divider()
st.header("2. 지역의 범죄율과 밤길 안전 인식 · 2024년")
st.write("범죄가 많이 발생한 지역일수록 밤길이 덜 안전하다고 느낄까요? 각 점은 한 시도입니다.")
st.caption("범죄율: 인구 10만 명당 발생건수 · 밤길 안전: 매우 안전 또는 비교적 안전하다고 응답한 비율")
regions = pd.read_csv(Path(__file__).with_name("regional_2024.csv"))
chosen = st.multiselect("비교할 시도", regions["지역"].tolist(), default=regions["지역"].tolist())
subset = regions[regions["지역"].isin(chosen)]
if subset.empty:
    st.info("시도를 하나 이상 선택하면 지역별 결과가 표시됩니다.")
else:
    x,y,z=st.columns(3)
    x.metric("선택한 시도", f"{len(subset)}곳")
    y.metric("선택 시도 평균 범죄율", f"{subset['범죄율_10만명당'].mean():,.1f}건")
    z.metric("선택 시도 평균 야간 안전도", f"{subset['야간안전_퍼센트'].mean():.1f}%")
    st.caption("선택 시도 평균은 각 시도를 동일한 비중으로 계산한 평균이며, 인구 가중 전국 평균이 아닙니다.")
    fig4=px.scatter(subset,x="범죄율_10만명당",y="야간안전_퍼센트",text="지역",
        labels={"범죄율_10만명당":"전체 범죄 발생 건수 (인구 10만 명당)","야간안전_퍼센트":"밤길이 안전하다고 응답한 비율 (%)"},
        hover_data={"지역":True,"범죄율_10만명당":":,.1f","야간안전_퍼센트":":.1f"},
        color_discrete_sequence=["#b65740"])
    fig4.update_traces(marker=dict(size=12),textposition="top center")
    fig4.update_layout(margin=dict(l=15,r=15,t=30,b=15))
    st.plotly_chart(fig4,width="stretch")
    with st.expander("선택 지역의 수치 보기"):
        st.dataframe(subset, hide_index=True, width="stretch")
st.caption("시도별 범죄율은 공소청 범죄분석통계, 추계인구를 바탕으로 한 전체 범죄 발생건수입니다. 야간 안전도는 13세 이상 응답자의 설문 추정치입니다. 범죄 유형·발생 장소가 밤길과 일치하지 않으며, 주민 인식과 사건 발생 지역의 인구가 반드시 같지 않습니다. 지역 간 상관관계는 개인에 대한 인과관계를 뜻하지 않습니다.")
st.markdown("[시도별 범죄율 출처](https://www.index.go.kr/unity/potal/eNara/sub/showStblGams3.do?freq=Y&idx_cd=F0226&period=N&stts_cd=F022601) · [야간보행 안전도 원 통계표](https://gsis.kwdi.re.kr/statHtml/statHtml.do?conn_path=I2&orgId=338&tblId=DT_1LIA022) · [야간보행 안전도 재인용 자료](https://www.ii.re.kr/storage/report/BB0000040231.pdf)")
