
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="東京23区 不動産価格分析",
    layout="wide"
)

st.title("東京23区 不動産価格分析")

# CSVファイルの読み込み
df = pd.read_csv(
    "Tokyo_20212_20261.csv",
    encoding="cp932"
)

# 価格を数値に変換
df["取引価格（総額）"] = pd.to_numeric(
    df["取引価格（総額）"].astype(str).str.replace(",", ""),
    errors="coerce"
)

# 建築年を数値に変換
df["建築年"] = pd.to_numeric(
    df["建築年"],
    errors="coerce"
)

# 取引時期から年と四半期を取得
period = df["取引時期"].astype(str)

df["年"] = pd.to_numeric(
    period.str.extract(r"(\d{4})")[0],
    errors="coerce"
)

df["四半期"] = pd.to_numeric(
    period.str.extract(r"第([1-4１-４])四半期")[0]
    .str.translate(str.maketrans("１２３４", "1234")),
    errors="coerce"
)

# 東京23区に絞り込み
df = df[
    df["市区町村名"].astype(str).str.endswith("区")
].copy()

# 欠損値と不正な価格を除去
df = df.dropna(
    subset=["市区町村名", "取引価格（総額）", "年", "四半期"]
)

df = df[
    df["取引価格（総額）"] > 0
].copy()

# 区ごとにIQRで外れ値を除去
clean_groups = []

for ku, group in df.groupby("市区町村名"):

    q1 = group["取引価格（総額）"].quantile(0.25)
    q3 = group["取引価格（総額）"].quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    filtered = group[
        (group["取引価格（総額）"] >= lower)
        & (group["取引価格（総額）"] <= upper)
    ].copy()

    clean_groups.append(filtered)

if len(clean_groups) == 0:
    st.error("分析できるデータがありません。")

else:
    df_clean = pd.concat(
        clean_groups,
        ignore_index=True
    )

    

    col1, col2, col3 = st.columns(3)

    col1.metric("取引件数", f"{len(df_clean):,}件")

    col2.metric(
        "対象の区",
        f"{df_clean['市区町村名'].nunique()}区"
    )

    col3.metric(
        "平均取引価格",
        f"{df_clean['取引価格（総額）'].mean() / 10000:,.1f}万円"
    )

    # 区の選択
    st.subheader("区ごとの価格比較")

    ku_list = sorted(
        df_clean["市区町村名"].unique()
    )

    selected_ku = st.selectbox(
        "比較する区を選択してください",
        ku_list
    )

    # 区と東京23区全体の平均価格
    ku_data = df_clean[
        df_clean["市区町村名"] == selected_ku
    ]

    selected_average = ku_data["取引価格（総額）"].mean()

    tokyo_average = df_clean[
        "取引価格（総額）"
    ].mean()

    comparison = pd.DataFrame({
        "項目": [selected_ku, "東京23区全体"],
        "平均取引価格（万円）": [
            selected_average / 10000,
            tokyo_average / 10000
        ]
    })

    comparison["平均取引価格（万円）"] = (
        comparison["平均取引価格（万円）"].round(1)
    )

    col1, col2 = st.columns(2)

    col1.metric(
        f"{selected_ku}の平均価格",
        f"{selected_average / 10000:,.1f}万円"
    )

    col2.metric(
        "東京23区全体の平均価格",
        f"{tokyo_average / 10000:,.1f}万円",
    )

    # 選択した区と東京23区全体の比較グラフ
    fig1 = go.Figure()

    fig1.add_trace(
        go.Bar(
            x=comparison["項目"],
            y=comparison["平均取引価格（万円）"],
            text=comparison["平均取引価格（万円）"],
            textposition="outside",
            name="平均取引価格"
        )
    )

    fig1.update_layout(
        title=f"{selected_ku}と東京23区全体の平均取引価格",
        yaxis_title="平均取引価格（万円）"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    # 四半期別の平均取引価格
    st.subheader("四半期別の価格推移")

    df_clean["時期"] = (
        df_clean["年"].astype(int).astype(str)
        + "年第"
        + df_clean["四半期"].astype(int).astype(str)
        + "四半期"
    )

    tokyo_quarterly = (
        df_clean.groupby(["年", "四半期"])["取引価格（総額）"]
        .mean()
        .reset_index()
        .sort_values(["年", "四半期"])
    )

    selected_quarterly = (
        df_clean[
            df_clean["市区町村名"] == selected_ku
        ]
        .groupby(["年", "四半期"])["取引価格（総額）"]
        .mean()
        .reset_index()
        .sort_values(["年", "四半期"])
    )

    tokyo_quarterly["時期"] = (
        tokyo_quarterly["年"].astype(int).astype(str)
        + "年第"
        + tokyo_quarterly["四半期"].astype(int).astype(str)
        + "四半期"
    )

    selected_quarterly["時期"] = (
        selected_quarterly["年"].astype(int).astype(str)
        + "年第"
        + selected_quarterly["四半期"].astype(int).astype(str)
        + "四半期"
    )

    fig2 = go.Figure()

    fig2.add_trace(
        go.Scatter(
            x=tokyo_quarterly["時期"],
            y=tokyo_quarterly["取引価格（総額）"] / 10000,
            mode="lines+markers",
            name="東京23区全体"
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=selected_quarterly["時期"],
            y=selected_quarterly["取引価格（総額）"] / 10000,
            mode="lines+markers",
            name=selected_ku
        )
    )

    fig2.update_layout(
        title=f"{selected_ku}と東京23区全体の四半期別価格推移",
        xaxis_title="時期",
        yaxis_title="平均取引価格（万円）",
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # 四半期別の価格一覧
    quarterly_table = tokyo_quarterly.copy()

    quarterly_table["平均取引価格（万円）"] = (
        quarterly_table["取引価格（総額）"] / 10000
    ).round(1)

    st.dataframe(
        quarterly_table[["時期", "平均取引価格（万円）"]],
        use_container_width=True
    )
