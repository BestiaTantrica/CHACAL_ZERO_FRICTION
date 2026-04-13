const fs = require('fs');

async function fetchData(symbol, interval, limit) {
    const url = `https://fapi.binance.com/fapi/v1/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`;
    const res = await fetch(url);
    const data = await res.json();
    return data.map(d => ({
        timestamp: d[0],
        open: parseFloat(d[1]),
        high: parseFloat(d[2]),
        low: parseFloat(d[3]),
        close: parseFloat(d[4]),
        volume: parseFloat(d[5])
    }));
}

function calcEMA(data, period) {
    const k = 2 / (period + 1);
    let ema = data[0].close;
    for (let i = 1; i < data.length; i++) {
        ema = (data[i].close - ema) * k + ema;
    }
    return ema;
}

function calcRSI(data, period) {
    let gains = 0, losses = 0;
    for(let i=1; i<=period; i++) {
        const change = data[data.length - 1 - period + i].close - data[data.length - 1 - period + i - 1].close;
        if(change > 0) gains += change;
        else losses -= change;
    }
    let avgGain = gains / period;
    let avgLoss = losses / period;
    if(avgLoss === 0) return 100;
    let rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
}

(async () => {
    const pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT"];
    const results = {};
    for (let pair of pairs) {
        try {
            const klines1h = await fetchData(pair, '1h', 150);
            const klines5m = await fetchData(pair, '5m', 50);
            const ema50 = calcEMA(klines1h, 50);
            const currentPrice = klines1h[klines1h.length - 1].close;
            const rsi1h = calcRSI(klines1h, 14);
            const rsi5m = calcRSI(klines5m, 14);
            const volCurrent = klines1h[klines1h.length - 1].volume;
            const last24 = klines1h.slice(-25, -1);
            const volAvg24 = last24.reduce((sum, k) => sum + k.volume, 0) / 24;
            
            let obj = {
                price: currentPrice,
                rsi_1h: rsi1h.toFixed(2),
                rsi_5m: rsi5m.toFixed(2),
                vol_current_vs_24h_avg: (volCurrent / volAvg24).toFixed(2)
            };
            
            if (pair === "BTCUSDT") {
                const distancePct = ((currentPrice - Math.abs(ema50)) / ema50) * 100;
                obj.ema50_1h = ema50.toFixed(2);
                obj.distance_ema50_pct = distancePct.toFixed(2);
                let regime = "";
                if (Math.abs(distancePct) < 4.3) {
                    if (Math.abs(distancePct) > 2.1 && (volCurrent / volAvg24) > 1.5) {
                        regime = "UMBRAL_ANTICIPADO -> Alto Volumen, Alarma de Relevo";
                    } else {
                        regime = "LATERAL -> Lateral V4 Mando";
                    }
                } else if (distancePct >= 4.3) {
                    regime = "BULL_TREND -> Fox Volume Hunter";
                } else {
                    regime = "BEAR_TREND -> Sniper Bear";
                }
                obj.regime = regime;
            }
            results[pair] = obj;
        } catch(e) { }
    }
    fs.writeFileSync('CHACAL_MARKET_DUMP_UTF8.json', JSON.stringify(results, null, 2), 'utf8');
})();
