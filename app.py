
import streamlit as st

from utils.data_loader import load_data
from utils.analysis import get_ward_summary


st.set_page_config(
    page_title="東京23区 不動産価格分析",
    page_icon="🏠",
    layout="wide"
)

# タイトル
st.title("🏠 東京23区 不動産価格分析")
st.subheader("東京都23区の不動産取引価格を可視化・分析")

st.write(
    """
    国土交通省の不動産取引データをもとに、
    東京23区の不動産価格をさまざまな視点から分析できるアプリです。
    
    地域ごとの価格差や、面積・築年数による価格の違いを
    地図やグラフを使って確認できます。
    """
)

st.divider()

# データ読み込み
df = load_data()
ward_summary = get_ward_summary(df)

# 基本情報
st.subheader("📊 データ概要")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("対象地域", "東京都23区")

with col2:
    st.metric("取引データ数", f"{len(df):,}件")

with col3:
    st.metric("区の数", f"{df['市区町村名'].nunique()}区")

st.divider()

# 機能紹介
st.subheader("🔍 主な機能")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🗺️ 地図")
    st.write(
        "各区の平均取引価格を地図上に表示します。"
        "円の大きさと色から地域ごとの価格差を比較できます。"
    )

    st.markdown("### 🔎 不動産検索")
    st.write(
        "区・面積・築年数などの条件を指定して、"
        "該当する不動産取引データを検索できます。"
    )

with col2:
    st.markdown("### 📈 データ分析")
    st.write(
        "年度ごとの価格推移や、区ごとの価格ランキング、"
        "面積・築年数による価格の違いを分析できます。"
    )

    st.markdown("### ⭐ お気に入り")
    st.write(
        "気になる不動産情報をお気に入りとして"
        "管理できる機能です。"
    )

st.divider()

st.info(
    "左側のサイドバーから各機能を選択してください。"
)
