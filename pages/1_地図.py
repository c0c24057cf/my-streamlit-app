
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from pathlib import Path

from utils.data_loader import load_data


# ---------------------------------
# ページ設定
# ---------------------------------

st.set_page_config(
    page_title="東京23区 不動産価格マップ",
    page_icon="🗺️",
    layout="wide"
)

st.title("東京23区 不動産価格マップ")
st.write("東京23区の不動産取引価格を地図上で比較できます。")


# ---------------------------------
# データ読み込み
# ---------------------------------

df = load_data()

# 23区の一覧
TOKYO_WARDS = [
    "千代田区", "中央区", "港区", "新宿区",
    "文京区", "台東区", "墨田区", "江東区",
    "品川区", "目黒区", "大田区", "世田谷区",
    "渋谷区", "中野区", "杉並区", "豊島区",
    "北区", "荒川区", "板橋区", "練馬区",
    "足立区", "葛飾区", "江戸川区"
]

# 23区のデータに絞り込む
df["市区町村名"] = df["市区町村名"].astype(str).str.strip()

df = df[
    df["市区町村名"].isin(TOKYO_WARDS)
].copy()

# 取引価格を数値に変換
df["取引価格（総額）"] = pd.to_numeric(
    df["取引価格（総額）"],
    errors="coerce"
)

# 欠損値・0円のデータを除外
df = df.dropna(subset=["取引価格（総額）"])
df = df[df["取引価格（総額）"] > 0]

if df.empty:
    st.error("地図に表示できるデータがありません。")
    st.stop()


# ---------------------------------
# 区ごとの平均価格を計算
# ---------------------------------

ward_avg = (
    df.groupby("市区町村名")["取引価格（総額）"]
    .mean()
    .reset_index()
)

ward_avg.columns = ["ward_name", "average_price"]

# 平均価格の高い順に順位付け
ward_avg["rank"] = ward_avg["average_price"].rank(
    ascending=False,
    method="first"
)

# 5段階に分類
ward_avg["category"] = pd.qcut(
    ward_avg["rank"],
    q=5,
    labels=["赤", "橙", "黄", "緑", "青"]
)

# 色の設定
colors = {
    "赤": "#e53935",
    "橙": "#fb8c00",
    "黄": "#fdd835",
    "緑": "#43a047",
    "青": "#1e88e5"
}

ward_avg["color"] = ward_avg["category"].map(colors)


# ---------------------------------
# GeoJSON読み込み
# ---------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

geojson_path = BASE_DIR / "N03-21_13_210101.json"

try:
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

except FileNotFoundError:
    st.error(
        "GeoJSONファイルが見つかりません。"
        "プロジェクト直下に N03-21_13_210101.json を配置してください。"
    )
    st.stop()


# FeatureCollectionか確認
if geojson_data.get("type") != "FeatureCollection":
    st.error("GeoJSONの形式が正しくありません。")
    st.stop()


# ---------------------------------
# GeoJSONを23区に絞り込む
# ---------------------------------

features = []

for feature in geojson_data["features"]:

    properties = feature.get("properties", {})

    prefecture = properties.get("N03_001")
    municipality = properties.get("N03_004")

    if prefecture == "東京都" and municipality in TOKYO_WARDS:

        feature["properties"]["ward_name"] = municipality
        features.append(feature)


tokyo_geojson = {
    "type": "FeatureCollection",
    "features": features
}

if not features:
    st.error(
        "GeoJSONから東京23区のデータを取得できませんでした。"
        "GeoJSONの属性名を確認してください。"
    )
    st.stop()


# GeoJSONに存在する区だけを残す
geojson_wards = [
    feature["properties"]["ward_name"]
    for feature in features
]

ward_avg = ward_avg[
    ward_avg["ward_name"].isin(geojson_wards)
].copy()

if ward_avg.empty:
    st.error("価格データと地図データを対応付けられませんでした。")
    st.stop()


# ---------------------------------
# 地図表示
# ---------------------------------

fig = go.Figure()

for category, color in colors.items():

    category_data = ward_avg[
        ward_avg["category"] == category
    ]

    if category_data.empty:
        continue

    fig.add_trace(
        go.Choroplethmap(
            geojson=tokyo_geojson,
            locations=category_data["ward_name"],
            z=[1] * len(category_data),
            featureidkey="properties.ward_name",
            colorscale=[
                [0, color],
                [1, color]
            ],
            showscale=False,
            marker_line_width=1,
            marker_line_color="white",
            customdata=category_data[
                ["average_price", "rank"]
            ],
            hovertemplate=(
                "<b>%{location}</b><br>"
                "平均取引価格：%{customdata[0]:,.0f}円<br>"
                "価格順位：%{customdata[1]:.0f}位"
                "<extra></extra>"
            )
        )
    )


fig.update_layout(
    map={
        "style": "open-street-map",
        "center": {
            "lat": 35.68,
            "lon": 139.76
        },
        "zoom": 9
    },
    height=750,
    margin={
        "r": 0,
        "t": 0,
        "l": 0,
        "b": 0
    },
    legend_title_text="価格帯"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------------------------------
# 平均価格ランキング
# ---------------------------------

st.subheader("東京23区 平均取引価格ランキング")

ranking = ward_avg.sort_values(
    "average_price",
    ascending=False
).copy()

ranking["順位"] = range(1, len(ranking) + 1)

ranking = ranking[
    ["順位", "ward_name", "average_price", "category"]
]

ranking.columns = [
    "順位",
    "区名",
    "平均取引価格（円）",
    "価格帯"
]

st.dataframe(
    ranking,
    use_container_width=True,
    hide_index=True
)

