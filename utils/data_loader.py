 # CSV読み込み・前処理


import pandas as pd
from pathlib import Path

# 東京都23区
TOKYO_WARDS = [
    "千代田区", "中央区", "港区", "新宿区",
    "文京区", "台東区", "墨田区", "江東区",
    "品川区", "目黒区", "大田区", "世田谷区",
    "渋谷区", "中野区", "杉並区", "豊島区",
    "北区", "荒川区", "板橋区", "練馬区",
    "足立区", "葛飾区", "江戸川区"
]


def load_data():
    """不動産取引データを読み込み、23区に絞り込む"""

    file_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "Tokyo_20212_20261.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSVファイルが見つかりません: {file_path}"
        )

    try:
        df = pd.read_csv(file_path, encoding="cp932")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 東京都23区のデータだけを抽出
    df = df[df["市区町村名"].isin(TOKYO_WARDS)].copy()

    
    # 取引年を取得
    df["取引年"] = (
        df["取引時期"]
        .str.extract(r"(\d{4})")
        .astype(float)
    )

    # 建築年から「年」を取り除いて数値に変換
    construction_year = pd.to_numeric(
        df["建築年"].astype("string").str.replace("年", "", regex=False),
        errors="coerce"
    )

    # 築年数を計算
    df["築年数"] = df["取引年"] - construction_year


    # 価格・面積の外れ値を除外
    df["取引価格（総額）"] = pd.to_numeric(
        df["取引価格（総額）"], errors="coerce"
    )

    df["面積（㎡）"] = pd.to_numeric(
        df["面積（㎡）"], errors="coerce"
    )

    df = df[
        (df["取引価格（総額）"] > 0)
        & (df["取引価格（総額）"] < 100000000)
        & (df["面積（㎡）"] > 0)
        & (df["面積（㎡）"] < 500)
    ].copy()




    return df
