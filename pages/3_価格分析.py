import streamlit as st

from utils.data_loader import load_data
from utils.analysis import get_ward_summary, get_yearly_summary


st.set_page_config(
    page_title="東京23区 不動産価格分析",
    page_icon="📊",
    layout="wide"
)

st.title("東京23区 不動産価格分析")

st.write(
    "東京都23区の不動産取引価格を、区別・年別に分析します。"
)

# データ読み込み
df = load_data()

# 区ごとの平均取引価格
st.subheader("区ごとの平均取引価格")

ward_summary = get_ward_summary(df)

st.bar_chart(
    ward_summary.set_index("市区町村名")["平均価格"]
)

st.dataframe(
    ward_summary,
    hide_index=True,
    use_container_width=True
)

# 年ごとの平均取引価格
st.subheader("年ごとの平均取引価格の推移")

yearly_summary = get_yearly_summary(df)

st.line_chart(
    yearly_summary.set_index("取引年")["平均価格"]
)

st.dataframe(
    yearly_summary,
    hide_index=True,
    use_container_width=True
)