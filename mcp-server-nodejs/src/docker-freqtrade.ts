import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const WORKDIR = 'c:\\CHACAL_ZERO_FRICTION';

export async function dockerTool(args: { command: string, strategy?: string, config?: string, timerange?: string, extraArgs?: string }) {
    const { command, strategy, config = 'user_data/config_pure.json', timerange, extraArgs = '' } = args;

    let fullCommand = `docker-compose run --rm freqtrade ${command}`;
    
    if (strategy) fullCommand += ` --strategy ${strategy}`;
    if (config) fullCommand += ` --config /freqtrade/${config}`;
    if (timerange) fullCommand += ` --timerange ${timerange}`;
    if (extraArgs) fullCommand += ` ${extraArgs}`;

    try {
        const { stdout, stderr } = await execAsync(fullCommand, { cwd: WORKDIR });
        return {
            content: [
                { type: 'text', text: `Comando ejecutado: ${fullCommand}` },
                { type: 'text', text: `Salida:\n${stdout}` },
                { type: 'text', text: stderr ? `Errores/Warnings:\n${stderr}` : '' }
            ]
        };
    } catch (error: any) {
        return {
            content: [{ type: 'text', text: `Error al ejecutar Docker: ${error.message}` }],
            isError: true
        };
    }
}
