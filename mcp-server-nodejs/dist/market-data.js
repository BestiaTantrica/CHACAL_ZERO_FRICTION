"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.cryptoMarketTool = cryptoMarketTool;
const ccxt_1 = __importDefault(require("ccxt"));
const binance = new ccxt_1.default.binance({
    enableRateLimit: true,
    options: { defaultType: 'swap' } // Futuros de Binance
});
async function cryptoMarketTool(args) {
    const { symbol, action, timeframe = '1h', limit = 20 } = args;
    const formattedSymbol = symbol.toUpperCase().includes('/') ? symbol.toUpperCase() : `${symbol.toUpperCase()}/USDT:USDT`;
    try {
        switch (action) {
            case 'ticker':
                const ticker = await binance.fetchTicker(formattedSymbol);
                return {
                    content: [
                        { type: 'text', text: `Ticker para ${formattedSymbol}:` },
                        { type: 'text', text: `Precio Último: ${ticker.last}` },
                        { type: 'text', text: `Cambio 24h: ${ticker.percentage}%` },
                        { type: 'text', text: `Volumen: ${ticker.baseVolume}` }
                    ]
                };
            case 'ohlcv':
                const ohlcv = await binance.fetchOHLCV(formattedSymbol, timeframe, undefined, limit);
                const formattedOHLCV = ohlcv.map(candle => ({
                    timestamp: new Date(candle[0]).toISOString(),
                    open: candle[1],
                    high: candle[2],
                    low: candle[3],
                    close: candle[4],
                    volume: candle[5]
                }));
                return {
                    content: [
                        { type: 'text', text: `Velas OHLCV (${timeframe}) para ${formattedSymbol}:` },
                        { type: 'text', text: JSON.stringify(formattedOHLCV, null, 2) }
                    ]
                };
            default:
                return {
                    content: [{ type: 'text', text: `Acción desconocida: ${action}. Acciones disponibles: ticker, ohlcv` }],
                    isError: true
                };
        }
    }
    catch (error) {
        return {
            content: [{ type: 'text', text: `Error al conectar con Binance (CCXT): ${error.message}` }],
            isError: true
        };
    }
}
