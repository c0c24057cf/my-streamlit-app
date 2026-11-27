
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.data_loader import load_data


st.set_page_config(
    page_title="東京23区不動産分析",
    page_icon="📈",
    layout="wide"
)

st.title("東京23区不動産価格分析")


# データ読み込み
df = load_data()


# 価格を数値型に変換
df["取引価格（総額）"] = pd.to_numeric(
    df["取引価格（総額）"],
    errors="coerce"
)

# 区名の空白を除去
df["市区町村名"] = df["市区町村名"].astype(str).str.strip()

# 欠損値を除外
df = df.dropna(
    subset=["市区町村名", "取引価格（総額）", "取引時期"]
).copy()


# 外れ値をIQR法で除外
q1 = df["取引価格（総額）"].quantile(0.25)
q3 = df["取引価格（総額）"].quantile(0.75)
iqr = q3 - q1

df = df[
    (df["取引価格（総額）"] >= q1 - 1.5 * iqr) &
    (df["取引価格（総額）"] <= q3 + 1.5 * iqr)
].copy()


if df.empty:
    st.error("分析できるデータがありません。")
    st.stop()


# ==================================
# 区ごとの価格比較
# ==================================

st.subheader("区ごとの価格比較")


ward_avg = (
    df.groupby("市区町村名")["取引価格（総額）"]
    .mean()
    .round(0)
    .astype(int)
    .reset_index()
    .sort_values("取引価格（総額）", ascending=False)
)


fig1 = go.Figure()

fig1.add_trace(
    go.Bar(
        x=ward_avg["市区町村名"],
        y=ward_avg["取引価格（総額）"]
    )
)

fig1.update_layout(
    xaxis_title="区名",
    yaxis_title="平均取引価格（円）",
    yaxis=dict(tickformat=",.0f")
)

st.plotly_chart(fig1, use_container_width=True)

st.dataframe(
    ward_avg,
    use_container_width=True,
    hide_index=True
)


st.divider()


# ==================================
# 年別の価格変化
# ==================================

st.subheader("年別の価格変化（全体平均）")


df["年"] = pd.to_numeric(
    df["取引時期"].astype(str).str.extract(r"(\d{4})")[0],
    errors="coerce"
)


year_avg = (
    df.dropna(subset=["年"])
    .groupby("年")["取引価格（総額）"]
    .mean()
    .round(0)
    .astype(int)
    .reset_index()
    .sort_values("年")
)


year_avg["年"] = (
    year_avg["年"].astype(int).astype(str)
)


fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(
        x=year_avg["年"],
        y=year_avg["取引価格（総額）"],
        mode="lines+markers"
    )
)

fig2.update_layout(
    xaxis_title="年",
    yaxis_title="平均取引価格（円）",
    yaxis=dict(tickformat=",.0f")
)

st.plotly_chart(fig2, use_container_width=True)

st.dataframe(
    year_avg,
    use_container_width=True,
    hide_index=True
)


st.divider()


# ==================================
# 四半期別の価格変化
# ==================================

st.subheader("四半期別の価格変化（全体平均）")


# 取引時期から年と四半期を取得
period = df["取引時期"].astype(str)


df["年"] = pd.to_numeric(
    period.str.extract(r"(\d{4})")[0],
    errors="coerce"
)


df["四半期番号"] = pd.to_numeric(
    period.str.extract(r"第([1-4１-４])四半期")[0]
    .str.translate(str.maketrans("１２３４", "1234")),
    errors="coerce"
)


# 別の表記形式にも対応
missing = df["四半期番号"].isna()

df.loc[missing, "四半期番号"] = pd.to_numeric(
    period[missing].str.extract(r"([1-4１-４])四半期")[0]
    .str.translate(str.maketrans("１２３４", "1234")),
    errors="coerce"
)


# 四半期別平均価格を集計
quarter_avg = (
    df.dropna(subset=["年", "四半期番号"])
    .groupby(["年", "四半期番号"])["取引価格（総額）"]
    .mean()
    .round(0)
    .astype(int)
    .reset_index()
    .sort_values(["年", "四半期番号"])
)


# 表示用の時期ラベル
quarter_avg["時期"] = (
    quarter_avg["年"].astype(int).astype(str)
    + "年第"
    + quarter_avg["四半期番号"].astype(int).astype(str)
    + "四半期"
)


# 四半期別グラフ
fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=quarter_avg["時期"],
        y=quarter_avg["取引価格（総額）"],
        mode="lines+markers",
        marker=dict(size=7)
    )
)

fig3.update_layout(
    xaxis_title="時期",
    yaxis_title="平均取引価格（円）",
    yaxis=dict(tickformat=",.0f"),
    xaxis=dict(
        tickangle=-45,
        type="category"
    ),
    height=550
)

st.plotly_chart(fig3, use_container_width=True)

st.dataframe(
    quarter_avg,
    use_container_width=True,
    hide_index=True
)
