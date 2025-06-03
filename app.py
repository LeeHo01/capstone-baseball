# app.py - 클러스터명 갱신 Streamlit 앱

import streamlit as st
import pandas as pd

# 📁 GitHub Raw 파일 경로
URLS = {
    "타자_프로": "https://github.com/LeeHo01/capstone-baseball/raw/main/%ED%94%84%EB%A1%9C%ED%83%80%EC%9E%90%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81%EA%B2%B0%EA%B3%BC(4).xlsx",
    "타자_고교": "https://github.com/LeeHo01/capstone-baseball/raw/main/%EA%B3%A0%EA%B5%90_%ED%83%80%EC%9E%90_%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81(4).xlsx",
    "투수_프로": "https://github.com/LeeHo01/capstone-baseball/raw/main/%ED%94%84%EB%A1%9C%ED%88%AC%EC%88%98%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81_4%EA%B0%9C.xlsx",
    "투수_고교": "https://github.com/LeeHo01/capstone-baseball/raw/main/%EA%B3%A0%EA%B5%90%ED%88%AC%EC%88%98_%ED%81%B4%EB%9F%AC%EC%8A%A4%ED%84%B0%EB%A7%81_4%EA%B0%9C.xlsx"
}

POSITION_MAP = {
    "내야수": list(range(0, 4)),
    "외야수": list(range(5, 10)),
    "포수": [10]
}

# 클러스터 명칭 매핑 (최신 버전)
def get_cluster_names(role):
    if role == "타자":
        return {
            1: "작전형 타자", 2: "정예 중심타자", 3: "선구안+주루형", 4: "파워히터"
        }, {
            0: "선구안+주루형", 1: "작전형 타자", 2: "정예 중심타자", 3: "파워히터"
        }, {1: [1], 2: [2], 3: [0], 4: [3]}
    else:
        return {
            1: "선발형", 2: "제구형", 3: "강속구형", 4: "중간계투형"
        }, {
            0: "선발형", 1: "제구형", 2: "중간계투형", 3: "강속구형"
        }, {1: [0], 2: [1], 3: [3], 4: [2]}

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

for c in [1, 2, 3, 4]:
    label = pro_name[c]
    desired_ratio[c] = st.sidebar.slider(f"{label} 비율 (%)", 0, 100, 25) / 100

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
        min_pos_codes = None

    # 🧠 출력
    st.subheader("📊 우리 팀 클러스터 분포")
    for c, p in my_ratio.items():
        if c in pro_name:
            st.markdown(f"- **{pro_name[c]}** → {p:.1%}")

    st.subheader("😵 전략상 부족한 클러스터")
    st.markdown(f"- {[pro_name[c] for c in short_clusters if c in pro_name]}")
    if role == "타자":
        st.markdown(f"- 작전형 타자 비중 가장 높은 포지션: **{min_position}**")

    st.subheader("🎯 고교 선수 추천 결과")

    for c in short_clusters:
        hs_clusters = cluster_map.get(c, [])
        hs_cluster_labels = [hs_name.get(h, f"클러스터 {h}") for h in hs_clusters]

        if role == "타자":
            filtered = df_high[
                (df_high['cluster'].isin(hs_clusters)) &
                (df_high['포지션_encoded'].isin(min_pos_codes))
            ]
            filtered = filtered.sort_values(by='Probability_of_1', ascending=False).head(5)
            filtered = filtered[['이름', 'cluster', 'Probability_of_1']].rename(columns={'cluster': '고교 클러스터', 'Probability_of_1': '추천 확률'})
            filtered['고교 클러스터'] = filtered['고교 클러스터'].replace(hs_name)
        else:
            filtered = df_high[df_high['Cluster'].isin(hs_clusters)]
            filtered = filtered.sort_values(by='Probability_of_1', ascending=False).head(5)
            filtered = filtered[['이름', 'Cluster', 'Probability_of_1']].rename(columns={'Cluster': '고교 클러스터', 'Probability_of_1': '추천 확률'})
            filtered['고교 클러스터'] = filtered['고교 클러스터'].replace(hs_name)

        st.markdown(f"#### ✅ [{pro_name[c]}] → 고교 클러스터 {hs_cluster_labels}")
        st.dataframe(filtered)
else:
    st.info("👆 위에서 선수를 선택하세요.")
