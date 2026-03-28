import yahooFinance from 'yahoo-finance2';
import * as math from 'mathjs';
import ccxt from 'ccxt';

const binance = new ccxt.binance({ options: { defaultType: 'swap' } });

// Definición de tipos para evitar errores de compilación
interface HistoricalData {
    date: Date;
    open: number;
    high: number;
    low: number;
    close: number;
    adjClose?: number;
    volume: number;
}

export async function riskManagerTool(args: { action: string, params: any }) {
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
                const btcCloses: number[] = btcData.map(c => c[4] as number);

                let report = `Análisis de Correlación (Últimos ${days} días):\n`;

                for (const asset of assets) {
                    const macroData = await yahooFinance.historical(asset, { period1: startDate }) as unknown as HistoricalData[];
                    const macroCloses: number[] = macroData.map((d: HistoricalData) => d.close);
                    
                    const minLen = Math.min(btcCloses.length, macroCloses.length);
                    if (minLen > 0) {
                        const corr = (math.corr(btcCloses.slice(0, minLen), macroCloses.slice(0, minLen)) as unknown) as number;
                        report += `- BTC vs ${asset}: ${corr.toFixed(4)}\n`;
                    }
                }

                return { content: [{ type: 'text', text: report }] };

            case 'volatility_adjust':
                const { symbol, period = 14 } = params;
                const ohlcv = await binance.fetchOHLCV(symbol, '1d', undefined, period + 1);
                const closes: number[] = ohlcv.map(c => c[4] as number);
                const stdDev = (math.std(closes) as unknown) as number;
                const avgPrice = (math.mean(closes) as unknown) as number;
                const volPercent = (stdDev / avgPrice) * 100;

                return {
                    content: [{ type: 'text', text: `Volatilidad actual (${symbol}): ${volPercent.toFixed(2)}%. Sugerencia: Stop Loss dinámico a ${ (volPercent * 2).toFixed(2) }%` }]
                };

            default:
                return { content: [{ type: 'text', text: `Acción desconocida: ${action}` }], isError: true };
        }
    } catch (error: any) {
        return { content: [{ type: 'text', text: `Error en Risk Manager: ${error.message}` }], isError: true };
    }
}
