# 九澤担当：条件比較機能 ＋ 検索機能（Streamlit）
# 実行方法：  streamlit run app.py
# 同じフォルダに Tokyo_20212_20261.csv を置いてください。
import re
from pathlib import Path

import pandas as pd
import streamlit as st

CSV_PATH = "Tokyo_20212_20261.csv"
MIN_N = 30  # これ未満の件数は「参考値」と表示する

WARDS_23 = [
    "千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区", "江東区",
    "品川区", "目黒区", "大田区", "世田谷区", "渋谷区", "中野区", "杉並区", "豊島区",
    "北区", "荒川区", "板橋区", "練馬区", "足立区", "葛飾区", "江戸川区",
]
TYPES = ["宅地(土地と建物)", "宅地(土地)"]
REQUIRED_COLUMNS = [
    "市区町村名",
    "取引価格（総額）",
    "面積（㎡）",
    "取引時期",
    "建築年",
    "今後の利用目的",
    "種類",
]

# 区分け（right=False なので「以上〜未満」）
AREA_BINS = [0, 50, 75, 100, 150, 250, float("inf")]
AREA_LABELS = ["〜50㎡", "50〜75㎡", "75〜100㎡", "100〜150㎡", "150〜250㎡", "250㎡〜"]
AGE_BINS = [0, 5, 10, 20, 30, 40, 50, 200]
AGE_LABELS = ["0〜4年", "5〜9年", "10〜19年", "20〜29年", "30〜39年", "40〜49年", "50年〜"]


# ---------------------------------------------------------------- データ
@st.cache_data(show_spinner="データを読み込み中...")
def load_data(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="cp932", low_memory=False)
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ) as exc:
        raise ValueError(
            "CSVを読み込めませんでした。ファイルの場所、文字コード（CP932）、"
            "CSVの形式を確認してください。"
        ) from exc

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"CSVに必要な列がありません: {', '.join(missing)}")

    # 23区だけにする
    df = df[df["市区町村名"].isin(WARDS_23)].copy()
    if df.empty:
        raise ValueError("CSVに東京23区の取引データがありません。")

    # 数値に直す（「2000㎡以上」などは NaN になる）
    df["価格_万円"] = pd.to_numeric(df["取引価格（総額）"], errors="coerce") / 10000
    df["面積"] = pd.to_numeric(df["面積（㎡）"], errors="coerce")

    # 取引年（例：2026年第1四半期 → 2026）
    df["取引年"] = pd.to_numeric(df["取引時期"].astype(str).str.extract(r"(\d{4})年")[0])

    # 築年数 ＝ 取引年 − 建築年（建築年は「2005年」の形）
    byear = pd.to_numeric(df["建築年"].astype(str).str.extract(r"(\d{4})年")[0])
    df["築年数"] = df["取引年"] - byear
    df.loc[(df["築年数"] < 0) | (df["築年数"] > 100), "築年数"] = pd.NA

    df["住宅利用"] = df["今後の利用目的"].astype(str).str.contains("住宅")
    df = df.dropna(subset=["価格_万円", "面積"])

    # 外れ値：種類ごとに、価格と面積の上下1%を除外
    keep = pd.Series(True, index=df.index)
    for col in ["価格_万円", "面積"]:
        lo = df.groupby("種類")[col].transform(lambda s: s.quantile(0.01))
        hi = df.groupby("種類")[col].transform(lambda s: s.quantile(0.99))
        keep &= (df[col] >= lo) & (df[col] <= hi)
    df = df[keep]

    cols = ["種類", "市区町村名", "地区名", "取引時期", "価格_万円", "面積", "築年数", "住宅利用"]
    return df[cols].reset_index(drop=True)


# ---------------------------------------------------------------- 条件比較
def summarize(df: pd.DataFrame, col: str, bins, labels) -> pd.DataFrame:
    """区分ごとの件数・中央値・平均を求める"""
    d = df.dropna(subset=[col]).copy()
    d["区分"] = pd.cut(d[col], bins=bins, labels=labels, right=False)
    t = d.groupby("区分", observed=False)["価格_万円"].agg(["count", "median", "mean"])
    t.columns = ["件数", "中央値（万円）", "平均（万円）"]
    return t.round(0)


def spearman(df: pd.DataFrame, col: str) -> float:
    d = df.dropna(subset=[col])
    correlation = d[col].rank().corr(d["価格_万円"].rank())
    return correlation


def tab_compare(data: pd.DataFrame):
    st.subheader("条件比較")
    st.write("面積・築年数によって、取引価格がどう変わるかを比べます。")

    c1, c2 = st.columns(2)
    ptype = c1.selectbox("物件種別", TYPES, key="cmp_type")
    items = ["面積"] if ptype == "宅地(土地)" else ["面積", "築年数"]
    item = c2.radio("比べる条件", items, horizontal=True, key="cmp_item")
    if ptype == "宅地(土地)":
        st.info("「宅地(土地)」には建物がないため、築年数は比較できません。")

    df = data[data["種類"] == ptype]
    if df.empty:
        st.warning("該当するデータがありません。")
        return

    if item == "面積":
        bins, labels = AREA_BINS, AREA_LABELS
    else:
        bins, labels = AGE_BINS, AGE_LABELS
    table = summarize(df, item, bins, labels)

    if table["件数"].sum() == 0:
        st.warning("該当するデータがありません。")
        return

    correlation = spearman(df, item)
    if pd.isna(correlation):
        st.info("データのばらつきが少ないため、相関を計算できません。")
    else:
        st.metric(
            f"{item}と価格の相関（スピアマン）",
            f"{correlation:.2f}",
            help="+1に近いほど「大きいほど高い」、−1に近いほど「大きいほど安い」、0は関係が弱い",
        )
    st.write(f"**{item}の区分ごとの価格の中央値（万円）**")
    st.bar_chart(table["中央値（万円）"])
    st.dataframe(table)

    if (table["件数"] < MIN_N).any():
        st.info(f"件数が{MIN_N}件未満の区分は参考値です。")


# ---------------------------------------------------------------- 検索
def tab_search(data: pd.DataFrame):
    st.subheader("検索")
    st.write("条件を指定して、過去の取引データを絞り込みます。")

    with st.form("search_form"):
        wards = st.multiselect("区（複数選べます）", WARDS_23, key="s_wards")
        ptype = st.selectbox("物件種別", TYPES, key="s_type")
        c1, c2 = st.columns(2)
        a_min = c1.number_input("面積の最小（㎡）", 0, 2000, 50, 5, key="s_amin")
        a_max = c2.number_input("面積の最大（㎡）", 0, 2000, 150, 5, key="s_amax")
        no_age = ptype == "宅地(土地)"
        age = st.slider("築年数（年）", 0, 100, (0, 100), disabled=no_age, key="s_age")
        submitted = st.form_submit_button("検索")

    if not submitted:
        return

    # 例外のチェック
    if not wards:
        st.warning("区を1つ以上選んでください。")
        return
    if a_min > a_max:
        st.error("面積の最小値が最大値より大きくなっています。入力を直してください。")
        return

    df = data[(data["種類"] == ptype) & (data["市区町村名"].isin(wards))]
    df = df[(df["面積"] >= a_min) & (df["面積"] <= a_max)]
    if no_age:
        st.info("「宅地(土地)」は築年数がないため、築年数の条件は使っていません。")
    else:
        df = df[df["築年数"].between(age[0], age[1])]

    if df.empty:
        st.warning("条件に該当するデータがありません。条件をゆるめてください。")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("件数", f"{len(df):,}件")
    c2.metric("平均価格", f"{df['価格_万円'].mean():,.0f}万円")
    c3.metric("中央値", f"{df['価格_万円'].median():,.0f}万円")
    if len(df) < MIN_N:
        st.info(f"件数が{MIN_N}件未満のため、平均・中央値は参考値です。")

    out = df.rename(columns={"市区町村名": "区", "面積": "面積（㎡）", "価格_万円": "価格（万円）"})
    st.dataframe(out.drop(columns=["住宅利用"]).sort_values("価格（万円）", ascending=False),
                 hide_index=True)


# ---------------------------------------------------------------- メイン
def main():
    st.set_page_config(page_title="東京23区 不動産取引価格", layout="centered")
    st.title("東京23区 不動産取引価格分析")
    st.caption("出典：国土交通省 不動産情報ライブラリ（過去の取引価格で、売り出し中の物件ではありません）")

    csv_path = Path(__file__).resolve().parent / CSV_PATH
    if not csv_path.exists():
        st.error(f"CSVファイル「{CSV_PATH}」が見つかりません。このファイルと同じフォルダに置いてください。")
        st.stop()
    try:
        data = load_data(str(csv_path))
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    if data.empty:
        st.error("利用できる取引データがありません。")
        st.stop()

    tab1, tab2 = st.tabs(["条件比較", "検索"])
    with tab1:
        tab_compare(data)
    with tab2:
        tab_search(data)


main()
