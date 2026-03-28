import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

// Import tools
import { analyzeStrategyTool } from './analyze-strategy.js';
import { freqtradeTool } from './freqtrade-api.js';
import { dockerTool } from './docker-freqtrade.js';
import { cryptoMarketTool } from './market-data.js';
import { riskManagerTool } from './risk-manager.js';
import { groqAnalysisTool } from './groq-bridge.js';

async function main() {
    const server = new Server(
        {
            name: 'chacal-mcp-server',
            version: '0.1.0',
        },
        {
            capabilities: {
                tools: {},
            },
        }
    );

    // Register tools
    server.setRequestHandler(ListToolsRequestSchema, async () => {
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
                {
                    name: 'groq_intel_analysis',
                    description: 'Advanced AI analysis for trading logs and complex data using Groq (Free)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            prompt: {
                                type: 'string',
                                description: 'The question or task for Groq',
                            },
                            context: {
                                type: 'string',
                                description: 'The data or logs to analyze',
                            }
                        },
                        required: ['prompt'],
                    },
                },
                {
                    name: 'aws_ssh_control',
                    description: 'Execute SSH or SCP commands on AWS instance',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            command: {
                                type: 'string',
                                description: 'The SSH or SCP command to execute',
                                required: true
                            },
                            type: {
                                type: 'string',
                                enum: ['ssh', 'scp'],
                                description: 'Type of command: ssh or scp',
                                required: true
                            },
                            pemPath: {
                                type: 'string',
                                description: 'Path to the .pem key file',
                                default: 'llave-sao-paulo.pem'
                            }
                        },
                        required: ['command', 'type'],
                    },
                },
            ],
        };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        switch (name) {
            case 'analyze_strategy':
                return await analyzeStrategyTool(args as any);
            case 'freqtrade_control':
                return await freqtradeTool(args as any);
            case 'docker_freqtrade':
                return await dockerTool(args as any);
            case 'crypto_market_intel':
                return await cryptoMarketTool(args as any);
            case 'risk_manager':
                return await riskManagerTool(args as any);
            case 'groq_intel_analysis':
                return await groqAnalysisTool(args as any);
            case 'aws_ssh_control':
                const commandArgs = args as any;
                
                return new Promise((resolve) => {
                    let cmd = commandArgs.command;
                    if (commandArgs.type === 'ssh' && !cmd.includes('ssh')) {
                        cmd = `ssh -o StrictHostKeyChecking=no -i "${commandArgs.pemPath || 'C:\\CHACAL_ZERO_FRICTION\\llave-sao-paulo.pem'}" ec2-user@15.229.158.221 "${commandArgs.command}"`;
                    } else if (commandArgs.type === 'scp' && !cmd.includes('scp')) {
                         cmd = `scp -o StrictHostKeyChecking=no -i "${commandArgs.pemPath || 'C:\\CHACAL_ZERO_FRICTION\\llave-sao-paulo.pem'}" "${commandArgs.command}" ec2-user@15.229.158.221:/home/ec2-user/freqtrade/user_data/strategies/`;
                    }

                    const { exec } = require('child_process');
                    exec(cmd, (error: any, stdout: string, stderr: string) => {
                        if (error) {
                            resolve({
                                content: [{ type: 'text', text: `Error: ${error.message}\nStderr: ${stderr}` }],
                                isError: true
                            });
                            return;
                        }
                        resolve({
                            content: [{ type: 'text', text: `Success:\n${stdout}\n${stderr}` }]
                        });
                    });
                });
                
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    });

    // Start the server
    const transport = new StdioServerTransport();
    await server.connect(transport);
}

main().catch((error) => {
    console.error('Server error:', error);
    process.exit(1);
});