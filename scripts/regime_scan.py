import pandas as pd


p = "/home/chacal/chacal_zero_friction/projects/bear/user_data/data/BTC_USDT_USDT-1h-futures.feather"
df = pd.read_feather(p).sort_values("date").reset_index(drop=True)

c = df["close"]
h = df["high"]
l = df["low"]

ema50 = c.ewm(span=50, adjust=False).mean()

d = c.diff()
g = d.clip(lower=0)
ls = (-d).clip(lower=0)
ag = g.ewm(alpha=1 / 14, adjust=False).mean()
al = ls.ewm(alpha=1 / 14, adjust=False).mean()
rs = ag / (al.replace(0, 1e-12))
rsi = 100 - (100 / (1 + rs))

pc = c.shift(1)
tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
atrm = atr.rolling(8).mean()

bear = c < ema50
active = atr > atrm

super_bear_strict = (bear & active & (rsi < 30)).fillna(False)
bear_normal_strict = (bear & active & (rsi >= 30) & (rsi < 45)).fillna(False)

# Versión operativa (menos estricta para detectar bloques útiles)
super_bear = (bear & (rsi < 35)).fillna(False)
bear_normal = (bear & (rsi >= 35) & (rsi < 50)).fillna(False)


def blocks(mask, name, min_hours=6):
    m = mask.to_numpy()
    runs = []
    on = False
    s = 0

    for i, v in enumerate(m):
        if v and not on:
            s = i
            on = True
        if on and ((not v) or i == len(m) - 1):
            e = i if (v and i == len(m) - 1) else i - 1
            if e - s + 1 >= min_hours:
                runs.append((s, e))
            on = False

    print(f"\n=== {name} ===")
    if not runs:
        print(f"sin bloques >={min_hours}h")
    for s, e in runs:
        print(df.loc[s, "date"], "->", df.loc[e, "date"], f"({e - s + 1}h)")


print("\nConteo velas strict:", {
    "super_bear_strict": int(super_bear_strict.sum()),
    "bear_normal_strict": int(bear_normal_strict.sum()),
})

blocks(super_bear, "SUPER_BEAR (operativo)", min_hours=6)
blocks(bear_normal, "BEAR_NORMAL (operativo)", min_hours=6)
print("\nCobertura BTC 1h:", df["date"].min(), "->", df["date"].max(), f"({len(df)} velas)")
