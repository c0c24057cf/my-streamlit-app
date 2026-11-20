
import streamlit as st

st.set_page_config(
    page_title="My Streamlit App",
    page_icon="🏠",
    layout="wide"
)

st.title("My Streamlit App")
st.write("Streamlitアプリのテストページです。")
import pandas as pd

df = pd.read_csv("Tokyo_20212_20261.csv", encoding="cp932")

df["取引価格（総額）"] = pd.to_numeric(
    df["取引価格（総額）"].astype(str).str.replace(",", ""),
    errors="coerce"
)

df["築年数"] = pd.to_numeric(
    df["建築年"].astype(str).str.extract(r"(\d{4})")[0],
    errors="coerce"
)

df["築年数"] = 2026 - df["築年数"]

df = df.dropna(subset=["取引価格（総額）", "築年数"])

Q1 = df["取引価格（総額）"].quantile(0.25)
Q3 = df["取引価格（総額）"].quantile(0.75)
IQR = Q3 - Q1

df = df[
    (df["取引価格（総額）"] >= Q1 - 1.5 * IQR) &
    (df["取引価格（総額）"] <= Q3 + 1.5 * IQR)
]

df.to_csv("Tokyo_23区_前処理.csv", index=False, encoding="utf-8-sig")

import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

df = pd.read_csv("Tokyo_23区_前処理.csv", encoding="utf-8-sig")

# 区ごとの平均価格
ward_avg = df.groupby("市区町村名")["取引価格（総額）"].mean().sort_values()

plt.figure(figsize=(12, 6))
plt.plot(ward_avg.index, ward_avg.values, marker="o")
plt.xticks(rotation=90)
plt.xlabel("区")
plt.ylabel("平均取引価格（円）")
plt.title("区ごとの平均取引価格")
plt.tight_layout()
plt.show()

# 年ごとの平均価格
year_avg = df.groupby("年")["取引価格（総額）"].mean().sort_index()

plt.figure(figsize=(10, 6))
plt.plot(year_avg.index, year_avg.values, marker="o")
plt.xlabel("年")
plt.ylabel("平均取引価格（円）")
plt.title("年ごとの平均取引価格")
plt.grid(True)
plt.tight_layout()
plt.show()