
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="東京23区不動産分析", layout="wide")
st.title("東京23区不動産価格分析")

df = pd.read_csv("Tokyo_20212_20261.csv", encoding="cp932")

wards = [
    "千代田区", "中央区", "港区", "新宿区", "文京区",
    "台東区", "墨田区", "江東区", "品川区", "目黒区",
    "大田区", "世田谷区", "渋谷区", "中野区", "杉並区",
    "豊島区", "北区", "荒川区", "板橋区", "練馬区",
    "足立区", "葛飾区", "江戸川区"
]

df["市区町村名"] = df["市区町村名"].astype(str).str.strip()
df = df[df["市区町村名"].isin(wards)].copy()

df["取引価格（総額）"] = pd.to_numeric(
    df["取引価格（総額）"].astype(str).str.replace(",", ""),
    errors="coerce"
)

df["建築年"] = df["建築年"].astype(str).str.extract(r"(\d{4})")
df["建築年"] = pd.to_numeric(df["建築年"], errors="coerce")
df["築年数"] = 2026 - df["建築年"]

df = df.dropna(subset=["市区町村名", "取引価格（総額）"])

q1 = df["取引価格（総額）"].quantile(0.25)
q3 = df["取引価格（総額）"].quantile(0.75)
iqr = q3 - q1

df = df[
    (df["取引価格（総額）"] >= q1 - 1.5 * iqr) &
    (df["取引価格（総額）"] <= q3 + 1.5 * iqr)
].copy()

st.subheader("区ごとの価格比較(2026年)")

ward_avg = (
    df.groupby("市区町村名")["取引価格（総額）"]
    .mean()
    .round(0)
    .astype(int)
    .reset_index()
    .sort_values("取引価格（総額）", ascending=False)
)

fig1 = go.Figure()

fig1.add_trace(go.Bar(
    x=ward_avg["市区町村名"],
    y=ward_avg["取引価格（総額）"]
))

fig1.update_layout(
    xaxis_title="区名",
    yaxis_title="平均取引価格（円）",
    yaxis=dict(tickformat=",.0f")
)

st.plotly_chart(fig1, use_container_width=True)
st.dataframe(ward_avg, use_container_width=True, hide_index=True)

st.divider()

st.subheader("年別の価格変化(全体平均)")

if "年" in df.columns:
    df["年"] = pd.to_numeric(df["年"], errors="coerce")
else:
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

year_avg["年"] = year_avg["年"].astype(int).astype(str)

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=year_avg["年"],
    y=year_avg["取引価格（総額）"],
    mode="lines+markers"
))

fig2.update_layout(
    xaxis_title="年",
    yaxis_title="平均取引価格（円）",
    yaxis=dict(tickformat=",.0f")
)

st.plotly_chart(fig2, use_container_width=True)
st.dataframe(year_avg, use_container_width=True, hide_index=True)

st.divider()

st.subheader("四半期別の価格変化(全体平均)")

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

# 四半期番号が取得できない場合は、別の形式にも対応
missing = df["四半期番号"].isna()

df.loc[missing, "四半期番号"] = pd.to_numeric(
    period[missing].str.extract(r"([1-4１-４])四半期")[0]
    .str.translate(str.maketrans("１２３４", "1234")),
    errors="coerce"
)

quarter_avg = (
    df.dropna(subset=["年", "四半期番号"])
    .groupby(["年", "四半期番号"])["取引価格（総額）"]
    .mean()
    .round(0)
    .astype(int)
    .reset_index()
    .sort_values(["年", "四半期番号"])
)

quarter_avg["時期"] = (
    quarter_avg["年"].astype(int).astype(str)
    + "年第"
    + quarter_avg["四半期番号"].astype(int).astype(str)
    + "四半期"
)

fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=quarter_avg["時期"],
    y=quarter_avg["取引価格（総額）"],
    mode="lines+markers",
    marker=dict(size=7)
))

fig3.update_layout(
    xaxis_title="時期",
    yaxis_title="平均取引価格（円）",
    yaxis=dict(tickformat=",.0f"),
    xaxis=dict(
        tickangle=-45,
        type="category",
        tickmode="linear"
    ),
    height=550
)

st.plotly_chart(fig3, use_container_width=True)
st.dataframe(quarter_avg, use_container_width=True, hide_index=True)
