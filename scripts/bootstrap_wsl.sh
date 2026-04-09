#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-${HOME}/chacal_zero_friction}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[BOOTSTRAP] ROOT=$ROOT"

# 1) Estructura base
mkdir -p "$ROOT"/{scripts,shared/strategies,shared/params,research/notebooks,research/regime_selector,state,skills}
mkdir -p "$ROOT/projects/bear/user_data"/{configs,data,backtest_results,hyperopt_results,logs}
mkdir -p "$ROOT/projects/bull/user_data"/{configs,data,backtest_results,hyperopt_results,logs}

# 2) Venv + Freqtrade
if [ ! -d "$ROOT/.venv" ]; then
  "$PYTHON_BIN" -m venv "$ROOT/.venv"
fi
source "$ROOT/.venv/bin/activate"
pip install --upgrade pip wheel setuptools
pip install freqtrade

# 3) Symlinks de estrategias compartidas
ln -sfn "$ROOT/shared/strategies" "$ROOT/projects/bear/user_data/strategies"
ln -sfn "$ROOT/shared/strategies" "$ROOT/projects/bull/user_data/strategies"

# 4) Archivos base
if [ ! -f "$ROOT/.env" ] && [ -f "$ROOT/.env.example" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
fi

# 5) Config template Bear (solo si no existe)
BEAR_CFG="$ROOT/projects/bear/user_data/configs/config_backtest.json"
if [ ! -f "$BEAR_CFG" ]; then
cat > "$BEAR_CFG" << 'EOF'
{
  "bot_name": "CHACAL-BEAR-BACKTEST",
  "dry_run": true,
  "timeframe": "5m",
  "timeframe_detail": "1m",
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "max_open_trades": 8,
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "dataformat_ohlcv": "feather",
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "options": {
        "defaultType": "swap"
      }
    },
    "pair_whitelist": [
      "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT",
      "BNB/USDT:USDT", "XRP/USDT:USDT", "ADA/USDT:USDT",
      "AVAX/USDT:USDT", "LINK/USDT:USDT"
    ]
  },
  "pairlists": [{"method": "StaticPairList"}]
}
EOF
echo "[OK] Creado template config_backtest.json para BEAR"
fi

# 6) Migrar estrategias existentes desde Windows (si existen)
WIN_SRC_1="/mnt/c/CHACAL_ZERO_FRICTION/strategies"
WIN_SRC_2="/mnt/c/CHACAL_ZERO_FRICTION/PROJECT_SNIPER_AWS/user_data/strategies"

if [ -d "$WIN_SRC_1" ]; then
  cp "$WIN_SRC_1"/*.py "$ROOT/shared/strategies/" 2>/dev/null || true
  cp "$WIN_SRC_1"/*.json "$ROOT/shared/params/" 2>/dev/null || true
  echo "[OK] Estrategias migradas desde $WIN_SRC_1"
fi

if [ -d "$WIN_SRC_2" ]; then
  cp "$WIN_SRC_2"/*.py "$ROOT/shared/strategies/" 2>/dev/null || true
  echo "[OK] Estrategias migradas desde $WIN_SRC_2"
fi

echo "[OK] Bootstrap completo"
echo "Siguiente paso:"
echo "  source $ROOT/.venv/bin/activate"
echo "  cd $ROOT && make doctor"
