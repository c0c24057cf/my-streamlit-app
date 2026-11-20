 # データ集計・分析

import pandas as pd


def get_ward_summary(df):
    """区ごとの平均取引価格と取引件数を集計する"""

    summary = (
        df.groupby("市区町村名")
        .agg(
            平均価格=("取引価格（総額）", "mean"),
            取引件数=("取引価格（総額）", "count")
        )
        .reset_index()
    )

    # 円から万円に変換
    summary["平均価格"] = summary["平均価格"] / 10000

    # 平均価格の降順に並べる
    summary = summary.sort_values(
        "平均価格", ascending=False
    )

    return summary

def get_yearly_summary(df):
    """取引年ごとの平均価格と取引件数を集計する"""

    summary = (
        df.groupby("取引年")
        .agg(
            平均価格=("取引価格（総額）", "mean"),
            取引件数=("取引価格（総額）", "count")
        )
        .reset_index()
    )

    # 円から万円に変換
    summary["平均価格"] = summary["平均価格"] / 10000

    # 年順に並べる
    summary = summary.sort_values("取引年")

    return summary

def get_condition_summary(df):
    """面積・築年数ごとの平均価格を集計する"""

    df = df.copy()

    # 面積区分
    area_bins = [0, 50, 70, 100, 150, 500]
    area_labels = [
        "50㎡以下",
        "50～70㎡",
        "70～100㎡",
        "100～150㎡",
        "150㎡超"
    ]

    df["面積区分"] = pd.cut(
        df["面積（㎡）"],
        bins=area_bins,
        labels=area_labels
    )

    # 築年数区分
    age_bins = [-1, 5, 10, 20, 30, 1000]
    age_labels = [
        "築5年以内",
        "築6～10年",
        "築11～20年",
        "築21～30年",
        "築30年超"
    ]

    df["築年数区分"] = pd.cut(
        df["築年数"],
        bins=age_bins,
        labels=age_labels
    )

    # 面積区分ごとの平均価格
    area_summary = (
        df.groupby("面積区分", observed=False)
        .agg(平均価格=("取引価格（総額）", "mean"))
        .reset_index()
    )

    # 築年数区分ごとの平均価格
    age_summary = (
        df.groupby("築年数区分", observed=False)
        .agg(平均価格=("取引価格（総額）", "mean"))
        .reset_index()
    )

    # 円から万円に変換
    area_summary["平均価格"] /= 10000
    age_summary["平均価格"] /= 10000

    return area_summary, age_summary


from utils.ward_coordinates import WARD_COORDINATES


def get_map_data(df):
    """区ごとの平均価格と座標を結合する"""

    # 区ごとの平均価格を集計
    summary = get_ward_summary(df)

    # 座標データをDataFrameに変換
    coordinates = pd.DataFrame(
        [
            {
                "市区町村名": ward,
                "latitude": lat,
                "longitude": lon
            }
            for ward, (lat, lon) in WARD_COORDINATES.items()
        ]
    )

    # 平均価格データと座標を結合
    map_data = summary.merge(
        coordinates,
        on="市区町村名",
        how="left"
    )

    return map_data
