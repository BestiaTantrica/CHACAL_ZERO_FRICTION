"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const index_js_1 = require("@modelcontextprotocol/sdk/server/index.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const types_js_1 = require("@modelcontextprotocol/sdk/types.js");
// Import tools
const analyze_strategy_js_1 = require("../tools/analyze-strategy.js");
const freqtrade_api_js_1 = require("../tools/freqtrade-api.js");
const docker_freqtrade_js_1 = require("../tools/docker-freqtrade.js");
const market_data_js_1 = require("../tools/market-data.js");
const risk_manager_js_1 = require("../tools/risk-manager.js");
async function main() {
    const server = new index_js_1.Server({
        name: 'chacal-mcp-server',
        version: '0.1.0',
    }, {
        capabilities: {
            tools: {},
        },
    });
    // Register tools
    server.setRequestHandler(types_js_1.ListToolsRequestSchema, async () => {
        return {
            tools: [
                {
                    name: 'analyze_strategy',
                    description: 'Analyze a trading strategy and provide insights',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            strategyPath: {
                                type: 'string',
                                description: 'Path to the strategy file to analyze',
                            },
                            analysisType: {
                                type: 'string',
                                enum: ['performance', 'risk', 'optimization'],
                                description: 'Type of analysis to perform',
                            },
                        },
                        required: ['strategyPath', 'analysisType'],
                    },
                },
                {
                    name: 'freqtrade_control',
                    description: 'Control your Freqtrade bot (status, profit, daily, reload_strategy, balance)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            action: {
                                type: 'string',
                                enum: ['status', 'profit', 'daily', 'reload_strategy', 'balance'],
                                description: 'The action to perform',
                            },
                        },
                        required: ['action'],
                    },
                },
                {
                    name: 'docker_freqtrade',
                    description: 'Run Freqtrade docker commands (backtesting, hyperopt, list-data)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            command: {
                                type: 'string',
                                enum: ['backtesting', 'hyperopt', 'list-data'],
                                description: 'The freqtrade command to run',
                            },
                            strategy: {
                                type: 'string',
                                description: 'Strategy name to use',
                            },
                            config: {
                                type: 'string',
                                description: 'Relative path to config file from user_data',
                                default: 'config_pure.json'
                            },
                            timerange: {
                                type: 'string',
                                description: 'Timerange for the command (e.g. 20250101-)',
                            },
                            extraArgs: {
                                type: 'string',
                                description: 'Additional arguments for the command',
                            }
                        },
                        required: ['command'],
                    },
                },
                {
                    name: 'crypto_market_intel',
                    description: 'Get real-time market data from Binance (ticker, OHLCV)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            symbol: {
                                type: 'string',
                                description: 'Cryptocurrency symbol (e.g. BTC/USDT:USDT)',
                            },
                            action: {
                                type: 'string',
                                enum: ['ticker', 'ohlcv'],
                                description: 'The market action to perform',
                            },
                            timeframe: {
                                type: 'string',
                                enum: ['1m', '5m', '1h', '1d'],
                                description: 'Timeframe for OHLCV data',
                                default: '1h'
                            },
                        },
                        required: ['symbol', 'action'],
                    },
                },
                {
                    name: 'risk_manager',
                    description: 'Professional Risk & Capital Management (Kelly, Correlation, Volatility)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            action: {
                                type: 'string',
                                enum: ['calculate_kelly', 'macro_correlation', 'volatility_adjust'],
                                description: 'The risk action to perform',
                            },
                            params: {
                                type: 'object',
                                description: 'Parameters for the risk action',
                            }
                        },
                        required: ['action', 'params'],
                    },
                },
            ],
        };
    });
    server.setRequestHandler(types_js_1.CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        switch (name) {
            case 'analyze_strategy':
                return await (0, analyze_strategy_js_1.analyzeStrategyTool)(args);
            case 'freqtrade_control':
                return await (0, freqtrade_api_js_1.freqtradeTool)(args);
            case 'docker_freqtrade':
                return await (0, docker_freqtrade_js_1.dockerTool)(args);
            case 'crypto_market_intel':
                return await (0, market_data_js_1.cryptoMarketTool)(args);
            case 'risk_manager':
                return await (0, risk_manager_js_1.riskManagerTool)(args);
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    });
    // Start the server
    const transport = new stdio_js_1.StdioServerTransport();
    await server.connect(transport);
}
main().catch((error) => {
    console.error('Server error:', error);
    process.exit(1);
});
