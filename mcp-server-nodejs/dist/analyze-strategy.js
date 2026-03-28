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
Object.defineProperty(exports, "__esModule", { value: true });
exports.analyzeStrategyTool = analyzeStrategyTool;
const fs = __importStar(require("fs"));
async function analyzeStrategyTool(args) {
    const { strategyPath, analysisType } = args;
    try {
        // Read the strategy file
        const strategyContent = fs.readFileSync(strategyPath, 'utf8');
        let analysis;
        switch (analysisType) {
            case 'performance':
                analysis = analyzePerformance(strategyContent);
                break;
            case 'risk':
                analysis = analyzeRisk(strategyContent);
                break;
            case 'optimization':
                analysis = analyzeOptimization(strategyContent);
                break;
            default:
                throw new Error(`Unknown analysis type: ${analysisType}`);
        }
        return {
            content: [
                {
                    type: 'text',
                    text: analysis,
                },
            ],
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error analyzing strategy: ${error instanceof Error ? error.message : 'Unknown error'}`,
                },
            ],
        };
    }
}
function analyzePerformance(content) {
    // Simple performance analysis
    const indicators = extractIndicators(content);
    const riskManagement = extractRiskManagement(content);
    return `
## Performance Analysis

### Indicators Used:
${indicators.map(ind => `- ${ind}`).join('\n')}

### Risk Management:
${riskManagement.map(rm => `- ${rm}`).join('\n')}

### Recommendations:
1. Monitor indicator performance regularly
2. Backtest with different timeframes
3. Consider market conditions when using indicators
  `;
}
function analyzeRisk(content) {
    // Simple risk analysis
    const stopLoss = content.includes('stop_loss') ? 'Found' : 'Not found';
    const positionSizing = content.includes('position_size') ? 'Found' : 'Not found';
    const diversification = content.includes('diversification') ? 'Found' : 'Not found';
    return `
## Risk Analysis

### Risk Management Components:
- Stop Loss: ${stopLoss}
- Position Sizing: ${positionSizing}
- Diversification: ${diversification}

### Risk Assessment:
1. Ensure proper stop loss implementation
2. Use appropriate position sizing
3. Diversify across different assets
4. Monitor risk exposure regularly
  `;
}
function analyzeOptimization(content) {
    // Simple optimization analysis
    const parameters = extractParameters(content);
    const optimizationPoints = identifyOptimizationPoints(content);
    return `
## Optimization Analysis

### Parameters Found:
${parameters.map(param => `- ${param}`).join('\n')}

### Optimization Opportunities:
${optimizationPoints.map(point => `- ${point}`).join('\n')}

### Optimization Strategy:
1. Use grid search for parameter optimization
2. Implement cross-validation
3. Monitor for overfitting
4. Regular re-optimization recommended
  `;
}
function extractIndicators(content) {
    const indicators = [];
    const indicatorPatterns = [
        /ta\.sma/g,
        /ta\.ema/g,
        /ta\.rsi/g,
        /ta\.macd/g,
        /ta\.bollinger/g,
    ];
    for (const pattern of indicatorPatterns) {
        if (pattern.test(content)) {
            indicators.push(pattern.source.replace('ta\\.', ''));
        }
    }
    return indicators;
}
function extractRiskManagement(content) {
    const riskManagement = [];
    const riskPatterns = [
        /stop_loss/g,
        /take_profit/g,
        /position_size/g,
        /risk_management/g,
    ];
    for (const pattern of riskPatterns) {
        if (pattern.test(content)) {
            riskManagement.push(pattern.source);
        }
    }
    return riskManagement;
}
function extractParameters(content) {
    const parameters = [];
    const paramPattern = /(?:const|let|var)\s+(\w+)\s*=/g;
    let match;
    while ((match = paramPattern.exec(content)) !== null) {
        parameters.push(match[1]);
    }
    return parameters.slice(0, 10); // Limit to first 10 parameters
}
function identifyOptimizationPoints(content) {
    const optimizationPoints = [];
    //const optimizationPoints: never[] = [];
    if (content.includes('hardcoded')) {
        optimizationPoints.push('Replace hardcoded values with parameters');
    }
    if (content.includes('magic numbers')) {
        optimizationPoints.push('Extract magic numbers to configuration');
    }
    if (content.includes('single timeframe')) {
        optimizationPoints.push('Consider multi-timeframe analysis');
    }
    return optimizationPoints;
}
