SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

# ====== HARDWARE GUARDRAIL ======
# i3-4170 + 10GB RAM: mantener en 1 para evitar OOM.
JOBS ?= 1
EPOCHS ?= 100
TIMERANGE ?= 20240801-20240901

# ====== RUTAS ABSOLUTAS ======
ROOT := $(PWD)
FT := ~/.venv_freqtrade/bin/freqtrade

STRATEGY_PATH := $(ROOT)/strategies
SNIPER_STRATEGY_PATH := $(ROOT)/PROJECT_SNIPER_AWS/user_data/strategies

BEAR_USERDATA := $(ROOT)/PROJECT_SNIPER_AWS/user_data
BEAR_CONFIG := $(BEAR_USERDATA)/configs/config_backtest.json
BEAR_DATADIR := $(BEAR_USERDATA)/data/binance/futures
BEAR_STRATEGY ?= ChacalSniper_Bear_ULTRA

BULL_USERDATA := $(ROOT)/CHACAL_VOLUME_HUNTER/user_data
BULL_CONFIG := $(BULL_USERDATA)/configs/config_backtest.json
BULL_DATADIR := $(BULL_USERDATA)/data/binance/futures
BULL_STRATEGY ?= ChacalVolumeHunter_V1

LATERAL_USERDATA := $(ROOT)/CHACAL_LATERAL/user_data
LATERAL_CONFIG := $(LATERAL_USERDATA)/configs/config_backtest.json
LATERAL_DATADIR := $(LATERAL_USERDATA)/data/binance/futures
LATERAL_STRATEGY ?= ChacalLateral_PureDNA62

.PHONY: help doctor list-data-bear list-data-bull list-data download-data-bear download-data-bull download-data download-data-bear-fresh download-data-bull-fresh backtest-bear backtest-bull backtest-bear-with-protections backtest-bull-with-protections hyperopt-bear-entry hyperopt-bear-risk hyperopt-bear-protection hyperopt-bull-entry hyperopt-bull-risk hyperopt-bull-protection sync-aws

help:
	@echo "=== CHACAL WSL COMMAND CENTER ==="
	@echo "make doctor"
	@echo "make list-data-bear"
	@echo "make list-data-bull"
	@echo "make download-data-bear TIMERANGE=20240801-20240901"
	@echo "make download-data-bear-fresh TIMERANGE=20240801-20240901"
	@echo "make backtest-bear TIMERANGE=20240801-20240901"
	@echo "make hyperopt-bear-entry EPOCHS=100"
	@echo "make hyperopt-bear-risk EPOCHS=100"
	@echo "make hyperopt-bear-protection EPOCHS=80"
	@echo "make sync-aws"

doctor:
	@test -x $(FT) || (echo "ERROR: no existe $(FT). Ejecuta scripts/bootstrap_wsl.sh" && exit 1)
	@$(FT) --version
	@echo "ROOT=$(ROOT)"
	@echo "BEAR_USERDATA=$(BEAR_USERDATA)"
	@echo "BULL_USERDATA=$(BULL_USERDATA)"
	@echo "JOBS=$(JOBS) (guardrail anti-OOM)"

# ====== LIST DATA ======
list-data: list-data-bear

list-data-bear:
	$(FT) list-data \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--trading-mode futures \
		--show-timerange

list-data-bull:
	$(FT) list-data \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--trading-mode futures \
		--show-timerange

list-data-lateral:
	$(FT) list-data \
		--config $(LATERAL_CONFIG) \
		--userdir $(LATERAL_USERDATA) \
		--datadir $(LATERAL_DATADIR) \
		--trading-mode futures \
		--show-timerange

# ====== DOWNLOAD DATA ======
download-data: download-data-bear

download-data-bear:
	$(FT) download-data \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--exchange binance \
		--trading-mode futures \
		--timeframes 1m 5m 1h \
		--timerange $(TIMERANGE)

download-data-bear-fresh:
	$(FT) download-data \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--exchange binance \
		--trading-mode futures \
		--timeframes 1m 5m 1h \
		--timerange $(TIMERANGE) \
		--erase

download-data-bull:
	$(FT) download-data \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--exchange binance \
		--trading-mode futures \
		--timeframes 1m 5m 1h \
		--timerange $(TIMERANGE)

download-data-bull-fresh:
	$(FT) download-data \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--exchange binance \
		--trading-mode futures \
		--timeframes 1m 5m 1h \
		--timerange $(TIMERANGE) \
		--erase

download-data-lateral:
	$(FT) download-data \
		--config $(LATERAL_CONFIG) \
		--userdir $(LATERAL_USERDATA) \
		--datadir $(LATERAL_DATADIR) \
		--exchange binance \
		--trading-mode futures \
		--timeframes 1m 5m 1h \
		--timerange $(TIMERANGE)

# ====== BACKTEST ======
backtest-bear:
	$(FT) backtesting \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--strategy-path $(SNIPER_STRATEGY_PATH) \
		--strategy $(BEAR_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--cache none \
		--export trades \
		--export-filename $(BEAR_USERDATA)/backtest_results/backtest_bear_$(TIMERANGE).json

backtest-bear-with-protections:
	$(FT) backtesting \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BEAR_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--cache none \
		--enable-protections

backtest-bull:
	$(FT) backtesting \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BULL_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--cache none \
		--export trades \
		--export-filename $(BULL_USERDATA)/backtest_results/backtest_bull_$(TIMERANGE).json

backtest-bull-with-protections:
	$(FT) backtesting \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BULL_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--cache none \
		--enable-protections

backtest-lateral:
	$(FT) backtesting \
		--config $(LATERAL_CONFIG) \
		--userdir $(LATERAL_USERDATA) \
		--datadir $(LATERAL_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(LATERAL_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--cache none \
		--export trades \
		--export-filename $(LATERAL_USERDATA)/backtest_results/backtest_lateral_$(TIMERANGE).json

# ====== HYPEROPT ======
hyperopt-bear-entry:
	$(FT) hyperopt \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BEAR_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--spaces buy sell \
		--epochs $(EPOCHS) -j $(JOBS)

hyperopt-bear-risk:
	$(FT) hyperopt \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BEAR_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--spaces roi stoploss trailing \
		--epochs $(EPOCHS) -j $(JOBS)

hyperopt-bear-protection:
	$(FT) hyperopt \
		--config $(BEAR_CONFIG) \
		--userdir $(BEAR_USERDATA) \
		--datadir $(BEAR_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BEAR_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--spaces protection \
		--epochs $(EPOCHS) -j $(JOBS)

hyperopt-bull-entry:
	$(FT) hyperopt \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BULL_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--spaces buy sell \
		--epochs $(EPOCHS) -j $(JOBS)

hyperopt-bull-risk:
	$(FT) hyperopt \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BULL_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--spaces roi stoploss trailing \
		--epochs $(EPOCHS) -j $(JOBS)

hyperopt-bull-protection:
	$(FT) hyperopt \
		--config $(BULL_CONFIG) \
		--userdir $(BULL_USERDATA) \
		--datadir $(BULL_DATADIR) \
		--strategy-path $(STRATEGY_PATH) \
		--strategy $(BULL_STRATEGY) \
		--timerange $(TIMERANGE) \
		--timeframe-detail 1m \
		--spaces protection \
		--epochs $(EPOCHS) -j $(JOBS)

# ====== AWS SYNC ======
sync-aws:
	@set -a; [ -f $(ROOT)/.env ] && . $(ROOT)/.env; set +a; \
	ssh -i $$AWS_PEM $$AWS_USER@$$AWS_HOST \
	"cd /home/ec2-user/freqtrade && git pull origin master && docker-compose restart"
