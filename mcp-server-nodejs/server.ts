
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Groq } from "groq-sdk";

// Configuración de Groq
const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY || "",
});

const server = new Server(
  {
    name: "chacal-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Listar herramientas disponibles
server.setRequestHandler(ListToolsRequestSchema, async () => {
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
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "ask_groq") {
    const prompt = request.params.arguments?.prompt as string;
    
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
    } catch (error: any) {
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
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("CHACAL MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
