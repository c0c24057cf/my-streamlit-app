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

st.subheader("データ概要")
st.write("データ件数:", len(df))
st.dataframe(df.head(), use_container_width=True)

st.divider()

st.subheader("区ごとの価格比較")

ward_avg = (
    df.groupby("市区町村名")["取引価格（総額）"]
    .mean()
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
    yaxis_title="平均取引価格（円）"
)

st.plotly_chart(fig1, use_container_width=True)
st.dataframe(ward_avg, use_container_width=True, hide_index=True)

st.divider()

st.subheader("時期ごとの価格変化")

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
    .reset_index()
    .sort_values("年")
)

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=year_avg["年"],
    y=year_avg["取引価格（総額）"],
    mode="lines+markers"
))

fig2.update_layout(
    xaxis_title="年",
    yaxis_title="平均取引価格（円）"
)

st.plotly_chart(fig2, use_container_width=True)
st.dataframe(year_avg, use_container_width=True, hide_index=True)