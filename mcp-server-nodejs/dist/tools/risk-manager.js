"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.riskManagerTool = riskManagerTool;
const yahoo_finance2_1 = __importDefault(require("yahoo-finance2"));
const math = __importStar(require("mathjs"));
const ccxt_1 = __importDefault(require("ccxt"));
const binance = new ccxt_1.default.binance({ options: { defaultType: 'swap' } });
async function riskManagerTool(args) {
    const { action, params } = args;
    try {
        switch (action) {
            case 'calculate_kelly':
                const { winRate, avgWin, avgLoss } = params;
                const b = Number(avgWin) / Math.abs(Number(avgLoss));
                const p = Number(winRate);
                const q = 1 - p;
                const kelly = (b * p - q) / b;
                return {
                    content: [{ type: 'text', text: `Kelly Fraction sugerida: ${(kelly * 100).toFixed(2)}% del capital.` }]
                };
            case 'macro_correlation':
                const { assets = ['^GSPC', 'GC=F', 'DX-Y.NYB'], days = 30 } = params;
                const endDate = new Date();
                const startDate = new Date();
                startDate.setDate(endDate.getDate() - days);
                const btcData = await binance.fetchOHLCV('BTC/USDT:USDT', '1d', startDate.getTime(), days);
                const btcCloses = btcData.map(c => c[4]);
                let report = `Análisis de Correlación (Últimos ${days} días):\n`;
                for (const asset of assets) {
                    const macroData = await yahoo_finance2_1.default.historical(asset, { period1: startDate });
                    const macroCloses = macroData.map((d) => d.close);
                    const minLen = Math.min(btcCloses.length, macroCloses.length);
                    if (minLen > 0) {
                        const corr = math.corr(btcCloses.slice(0, minLen), macroCloses.slice(0, minLen));
                        report += `- BTC vs ${asset}: ${corr.toFixed(4)}\n`;
                    }
                }
                return { content: [{ type: 'text', text: report }] };
            case 'volatility_adjust':
                const { symbol, period = 14 } = params;
                const ohlcv = await binance.fetchOHLCV(symbol, '1d', undefined, period + 1);
                const closes = ohlcv.map(c => c[4]);
                const stdDev = math.std(closes);
                const avgPrice = math.mean(closes);
                const volPercent = (stdDev / avgPrice) * 100;
                return {
                    content: [{ type: 'text', text: `Volatilidad actual (${symbol}): ${volPercent.toFixed(2)}%. Sugerencia: Stop Loss dinámico a ${(volPercent * 2).toFixed(2)}%` }]
                };
            default:
                return { content: [{ type: 'text', text: `Acción desconocida: ${action}` }], isError: true };
        }
    }
    catch (error) {
        return { content: [{ type: 'text', text: `Error en Risk Manager: ${error.message}` }], isError: true };
    }
}
