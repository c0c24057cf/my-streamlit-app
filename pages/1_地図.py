

import streamlit as st
import pydeck as pdk

from utils.data_loader import load_data
from utils.analysis import get_map_data


st.set_page_config(
    page_title="東京23区 不動産価格マップ",
    page_icon="🗺️",
    layout="wide"
)

st.title("東京23区 不動産価格マップ")

st.write(
    "各区の代表地点に、平均取引価格を円の大きさと色で表示しています。"
)

# データ読み込み
df = load_data()
map_data = get_map_data(df)

# 円の大きさを調整
map_data["radius"] = (
    map_data["平均価格"] * 0.6
)

# 平均価格に応じた色を設定
min_price = map_data["平均価格"].min()
max_price = map_data["平均価格"].max()

def get_color(price):
    ratio = (price - min_price) / (max_price - min_price)

    # 安い区：青、高い区：赤
    red = int(50 + 205 * ratio)
    blue = int(255 - 205 * ratio)

    return [red, 80, blue, 170]


map_data["color"] = map_data["平均価格"].apply(get_color)

# 地図の描画
layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_data,
    get_position="[longitude, latitude]",
    get_radius="radius",
    get_fill_color="color",
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(
    latitude=35.69,
    longitude=139.75,
    zoom=10,
    pitch=0,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "text": "{市区町村名}\n平均価格：{平均価格}万円\n取引件数：{取引件数}件"
    },
)

st.pydeck_chart(deck, use_container_width=True)

# 価格ランキング
st.subheader("区ごとの平均取引価格ランキング")

ranking = map_data[
    ["市区町村名", "平均価格", "取引件数"]
].sort_values("平均価格", ascending=False)

st.dataframe(
    ranking,
    hide_index=True,
    use_container_width=True
)
