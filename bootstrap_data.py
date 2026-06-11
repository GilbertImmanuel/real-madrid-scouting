import urllib.request, pyreadr
from pathlib import Path

BASE = ("https://raw.githubusercontent.com/JaseZiv/worldfootballR_data/"
        "master/data/fb_big5_advanced_season_stats/")
TABLES = ["standard", "shooting", "passing", "defense",
          "possession", "misc", "gca", "playing_time"]
SEASONS = [2021, 2022, 2023]                      # = 2020-21, 2021-22, 2022-23
RAW = Path("data/raw/fbref"); RAW.mkdir(parents=True, exist_ok=True)

for t in TABLES:
    fname = f"big5_player_{t}.rds"
    tmp = RAW / fname
    urllib.request.urlretrieve(BASE + fname, tmp)            # download frozen RDS
    df = list(pyreadr.read_r(str(tmp)).values())[0]          # read in pure Python
    df = df[df["Season_End_Year"].isin(SEASONS)].reset_index(drop=True)
    df.to_parquet(RAW / f"{t}.parquet")                      # fast local cache
    tmp.unlink()
    print(f"{t:14s} {df.shape}")