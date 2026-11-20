
import pandas as pd
import streamlit as st

from utils.data_loader import load_data

st.title("検索・条件比較")
st.caption("東京23区の過去の不動産取引データを条件別に分析できます。")

MIN_N = 30

WARDS_23 = [
    "千代田区", "中央区", "港区", "新宿区", "文京区",
    "台東区", "墨田区", "江東区", "品川区", "目黒区",
    "大田区", "世田谷区", "渋谷区", "中野区", "杉並区",
    "豊島区", "北区", "荒川区", "板橋区", "練馬区",
    "足立区", "葛飾区", "江戸川区"
]

TYPES = ["宅地(土地と建物)", "宅地(土地)"]

AREA_BINS = [0, 50, 75, 100, 150, 250, float("inf")]
AREA_LABELS = [
    "〜50㎡", "50〜75㎡", "75〜100㎡",
    "100〜150㎡", "150〜250㎡", "250㎡〜"
]

AGE_BINS = [0, 5, 10, 20, 30, 40, 50, 200]
AGE_LABELS = [
    "0〜4年", "5〜9年", "10〜19年",
    "20〜29年", "30〜39年", "40〜49年", "50年〜"
]


@st.cache_data
def get_data():
    return load_data()


def summarize(df, column, bins, labels):
    d = df.dropna(subset=[column]).copy()
    d["区分"] = pd.cut(
        d[column], bins=bins, labels=labels, right=False
    )

    result = (
        d.groupby("区分", observed=False)["取引価格（総額）"]
        .agg(["count", "median", "mean"])
    )

    result.columns = ["件数", "中央値（万円）", "平均（万円）"]
    result["中央値（万円）"] /= 10000
    result["平均（万円）"] /= 10000

    return result.round(0)




def tab_compare(data):
    st.subheader("条件比較")
    st.write("面積・築年数によって取引価格がどう変わるかを比較します。")

    c1, c2 = st.columns(2)

    ptype = c1.selectbox("物件種別", TYPES, key="cmp_type")

    items = ["面積（㎡）"] if ptype == "宅地(土地)" else ["面積（㎡）", "築年数"]
    item = c2.radio("比較する条件", items, horizontal=True)

    if ptype == "宅地(土地)":
        st.info("土地のみの取引には建物がないため、築年数は比較できません。")

    df = data[data["種類"] == ptype].copy()

    if df.empty:
        st.warning("該当するデータがありません。")
        return

    if item == "面積（㎡）":
        bins, labels = AREA_BINS, AREA_LABELS
    else:
        bins, labels = AGE_BINS, AGE_LABELS

    table = summarize(df, item, bins, labels)

    if table["件数"].sum() == 0:
        st.warning("該当するデータがありません。")
        return

    st.write(f"**{item}の区分ごとの価格中央値（万円）**")
    st.bar_chart(table["中央値（万円）"])
    st.dataframe(table, use_container_width=True)

    if (table["件数"] < MIN_N).any():
        st.info(f"{MIN_N}件未満の区分は参考値です。")


def tab_search(data):
    st.subheader("検索")
    st.write("条件を指定して過去の取引データを絞り込みます。")

    with st.form("search_form"):
        wards = st.multiselect("区", WARDS_23)
        ptype = st.selectbox("物件種別", TYPES)

        c1, c2 = st.columns(2)
        a_min = c1.number_input("面積の最小（㎡）", 0, 2000, 50, 5)
        a_max = c2.number_input("面積の最大（㎡）", 0, 2000, 150, 5)

        no_age = ptype == "宅地(土地)"
        age = st.slider(
            "築年数（年）", 0, 100, (0, 100),
            disabled=no_age
        )

        submitted = st.form_submit_button("検索")

    if not submitted:
        return

    if not wards:
        st.warning("区を1つ以上選んでください。")
        return

    if a_min > a_max:
        st.error("面積の最小値が最大値より大きくなっています。")
        return

    df = data[
        (data["種類"] == ptype)
        & (data["市区町村名"].isin(wards))
    ].copy()

    df = df[
        (df["面積（㎡）"] >= a_min)
        & (df["面積（㎡）"] <= a_max)
    ]

    if not no_age:
        df = df[df["築年数"].between(age[0], age[1])]

    if df.empty:
        st.warning("条件に該当するデータがありません。")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("件数", f"{len(df):,}件")
    c2.metric("平均価格", f"{df['取引価格（総額）'].mean() / 10000:,.0f}万円")
    c3.metric("中央値", f"{df['取引価格（総額）'].median() / 10000:,.0f}万円")

    if len(df) < MIN_N:
        st.info(f"{MIN_N}件未満のため、価格は参考値です。")

    st.dataframe(
        df.sort_values("取引価格（総額）", ascending=False),
        hide_index=True,
        use_container_width=True
    )


def main():
    try:
        data = get_data()
    except Exception as exc:
        st.error(f"データの読み込みに失敗しました: {exc}")
        st.stop()

    tab1, tab2 = st.tabs(["条件比較", "検索"])

    with tab1:
        tab_compare(data)

    with tab2:
        tab_search(data)


main()
