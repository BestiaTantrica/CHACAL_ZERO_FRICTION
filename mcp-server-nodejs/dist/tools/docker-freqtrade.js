"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.dockerTool = dockerTool;
const child_process_1 = require("child_process");
const util_1 = require("util");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
const WORKDIR = 'c:\\CHACAL_ZERO_FRICTION';
async function dockerTool(args) {
    const { command, strategy, config = 'user_data/config_pure.json', timerange, extraArgs = '' } = args;
    let fullCommand = `docker-compose run --rm freqtrade ${command}`;
    if (strategy)
        fullCommand += ` --strategy ${strategy}`;
    if (config)
        fullCommand += ` --config /freqtrade/${config}`;
    if (timerange)
        fullCommand += ` --timerange ${timerange}`;
    if (extraArgs)
        fullCommand += ` ${extraArgs}`;
    try {
        const { stdout, stderr } = await execAsync(fullCommand, { cwd: WORKDIR });
        return {
            content: [
                { type: 'text', text: `Comando ejecutado: ${fullCommand}` },
                { type: 'text', text: `Salida:\n${stdout}` },
                { type: 'text', text: stderr ? `Errores/Warnings:\n${stderr}` : '' }
            ]
        };
    }
    catch (error) {
        return {
            content: [{ type: 'text', text: `Error al ejecutar Docker: ${error.message}` }],
            isError: true
        };
    }
}
