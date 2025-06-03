import streamlit as st
import pandas as pd

# 📁 GitHub Raw 파일 경로
URLS = {
    "타자_프로": "https://github.com/LeeHo01/capstone-baseball/blob/main/%ED%94%84%EB%A1%9C%ED%83%80%EC%9E%90%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81%EA%B2%B0%EA%B3%BC(4).xlsx",
    "타자_고교": "https://github.com/LeeHo01/capstone-baseball/blob/main/%EA%B3%A0%EA%B5%90%ED%83%80%EC%9E%90%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81_4%EA%B0%9C.xlsx",
    "투수_프로": "https://github.com/LeeHo01/capstone-baseball/blob/main/%ED%94%84%EB%A1%9C%ED%88%AC%EC%88%98%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81_4%EA%B0%9C.xlsx",
    "투수_고교": "https://github.com/LeeHo01/capstone-baseball/blob/main/%EA%B3%A0%EA%B5%90%ED%88%AC%EC%88%98_%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81_4%EA%B0%9C.xlsx"
}

POSITION_MAP = {
    "내야수": list(range(0, 4)),
    "외야수": list(range(5, 10)),
    "포수": [10]
}

# 클러스터 명칭 및 매핑
def get_cluster_names(role):
    if role == "타자":
        return {
            0: "거포형 타자",
            1: "선구안 기반 출루 타자",
            2: "타격 기반 출루 타자",
            3: "수비 및 주루 특화타자"
        }, {
            0: "거포형 타자",
            1: "선구안 기반 출루 타자",
            2: "타격 기반 출루 타자",
            3: "수비 및 주루 특화타자"
        }, {
            0: [3],
            1: [1],
            2: [2],
            3: [0]
        }
    else:
        return {
            0: "제구형",
            1: "불안정형",
            2: "선발형",
            3: "강속구형"
        }, {
            0: "선발형",
            1: "제구형",
            2: "불안정형",
            3: "강속구형"
        }, {
            0: [1],
            1: [],    # ❌ 불안정형은 추천하지 않음
            2: [0],
            3: [3]
        }

# ✅ Streamlit 시작
st.set_page_config(page_title="스카우트 추천 시스템", layout="wide")
st.title("⚾ 팀 구성 기반 선수 추천 시스템")

# 🧩 역할 선택
role = st.radio("선수 유형을 선택하세요", ["타자", "투수"], horizontal=True)

# 📦 데이터 불러오기
with st.spinner("데이터 불러오는 중..."):
    df_pro = pd.read_excel(URLS[f"{role}_프로"])
    df_high = pd.read_excel(URLS[f"{role}_고교"])

# 🎯 사용자 입력
all_names = df_pro['Name'].dropna().unique().tolist()
selected_names = st.multiselect("✅ 우리 팀 선수 선택", sorted(all_names))

# 🎚️ 비율 설정 슬라이더
st.sidebar.header("🎯 원하는 클러스터 비율 설정")
pro_name, hs_name, cluster_map = get_cluster_names(role)
desired_ratio = {}

for c in pro_name:
    label = f"{pro_name[c]} 비율 설정 (%)"
    desired_ratio[c] = st.sidebar.slider(label, 0, 100, 25) / 100

# 👇 본 분석 진행
if selected_names:
    df_my = df_pro[df_pro['Name'].isin(selected_names)]
    my_ratio = df_my['cluster'].value_counts(normalize=True)
    short_clusters = [c for c in desired_ratio if my_ratio.get(c, 0) < desired_ratio[c]]

    # 📌 타자의 경우 포지션 분석
    if role == "타자":
        boryu_ratio = {}
        for pos, codes in POSITION_MAP.items():
            subset = df_my[df_my['position'].isin(codes)]
            total = len(subset)
            boryu_count = len(subset[subset['cluster'] == 1])
            boryu_ratio[pos] = boryu_count / total if total > 0 else 0
        min_position = max(boryu_ratio, key=boryu_ratio.get)
        min_pos_codes = POSITION_MAP[min_position]
    else:
        min_pos_codes = None  # 투수는 포지션 없음

    # 🧠 출력
    st.subheader("📊 우리 팀 클러스터 분포")
    for c, p in my_ratio.items():
        st.markdown(f"- **{pro_name[c]}** → {p:.1%}")

    st.subheader("😵 전략상 부족한 클러스터")
    st.markdown(f"- {[pro_name[c] for c in short_clusters]}")
    if role == "타자":
        st.markdown(f"- 보류형 비중 가장 높은 포지션: **{min_position}**")

    st.subheader("🎯 고교 선수 추천 결과")

    for c in short_clusters:
        hs_clusters = cluster_map.get(c, [])
        if not hs_clusters:
            st.markdown(f"#### ⚠️ [{pro_name[c]}] 유형은 전략상 추천되지 않습니다.")
            continue

        hs_cluster_labels = [hs_name.get(h, f"클러스터 {h}") for h in hs_clusters]

        if role == "타자":
            filtered = df_high[
                (df_high['cluster'].isin(hs_clusters)) &
                (df_high['포지션_encoded'].isin(min_pos_codes))
            ]
            filtered = filtered.sort_values(by='Probability_of_1', ascending=False).head(5)
            filtered = filtered[['이름', 'cluster', 'Probability_of_1']].rename(
                columns={'cluster': '고교 클러스터', 'Probability_of_1': '추천 확률'})
            filtered['고교 클러스터'] = filtered['고교 클러스터'].replace(hs_name)
        else:
            filtered = df_high[df_high['Cluster'].isin(hs_clusters)]
            filtered = filtered.sort_values(by='Probability_of_1', ascending=False).head(5)
            filtered = filtered[['이름', 'Cluster', 'Probability_of_1']].rename(
                columns={'Cluster': '고교 클러스터', 'Probability_of_1': '추천 확률'})
            filtered['고교 클러스터'] = filtered['고교 클러스터'].replace(hs_name)

        st.markdown(f"#### ✅ [{pro_name[c]}] → 고교 클러스터 {hs_cluster_labels}")
        st.dataframe(filtered)

else:
    st.info("👆 위에서 선수를 선택하세요.")

