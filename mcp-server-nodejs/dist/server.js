"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const index_js_1 = require("@modelcontextprotocol/sdk/server/index.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const types_js_1 = require("@modelcontextprotocol/sdk/types.js");
const groq_sdk_1 = require("groq-sdk");
// Configuración de Groq
const groq = new groq_sdk_1.Groq({
    apiKey: process.env.GROQ_API_KEY || "",
});
const server = new index_js_1.Server({
    name: "chacal-mcp",
    version: "1.0.0",
}, {
    capabilities: {
        tools: {},
    },
});
// Listar herramientas disponibles
server.setRequestHandler(types_js_1.ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "ask_groq",
                description: "Realiza una consulta a Groq (LLM rápido) para análisis de trading.",
                inputSchema: {
                    type: "object",
                    properties: {
                        prompt: {
                            type: "string",
                            description: "El prompt para el modelo.",
                        },
                    },
                    required: ["prompt"],
                },
            },
        ],
    };
});
// Manejar llamadas a herramientas
server.setRequestHandler(types_js_1.CallToolRequestSchema, async (request) => {
    if (request.params.name === "ask_groq") {
        const prompt = request.params.arguments?.prompt;
        try {
            const completion = await groq.chat.completions.create({
                messages: [{ role: "user", content: prompt }],
                model: "llama3-70b-8192",
            });
            return {
                content: [
                    {
                        type: "text",
                        text: completion.choices[0]?.message?.content || "No hubo respuesta.",
                    },
                ],
            };
        }
        catch (error) {
            return {
                isError: true,
                content: [
                    {
                        type: "text",
                        text: `Error de Groq: ${error.message}`,
                    },
                ],
            };
        }
    }
    throw new Error("Herramienta no encontrada");
});
// Iniciar servidor
async function main() {
    const transport = new stdio_js_1.StdioServerTransport();
    await server.connect(transport);
    console.error("CHACAL MCP Server running on stdio");
}
main().catch((error) => {
    console.error("Fatal error in main():", error);
    process.exit(1);
});
