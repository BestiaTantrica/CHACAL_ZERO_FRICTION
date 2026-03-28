import axios from 'axios';

const FREQTRADE_API_URL = 'http://15.229.158.221:8080/api/v1';
const AUTH = {
    username: 'freqtrade',
    password: 'chacal2026'
};

export async function freqtradeTool(args: { action: string, params?: any }) {
    const { action, params = {} } = args;

    try {
        switch (action) {
            case 'status':
                const statusRes = await axios.get(`${FREQTRADE_API_URL}/status`, { auth: AUTH });
                return { content: [{ type: 'text', text: JSON.stringify(statusRes.data, null, 2) }] };

            case 'profit':
                const profitRes = await axios.get(`${FREQTRADE_API_URL}/profit`, { auth: AUTH });
                return { content: [{ type: 'text', text: JSON.stringify(profitRes.data, null, 2) }] };

            case 'daily':
                const dailyRes = await axios.get(`${FREQTRADE_API_URL}/daily`, { auth: AUTH, params: { days: params.days || 7 } });
                return { content: [{ type: 'text', text: JSON.stringify(dailyRes.data, null, 2) }] };

            case 'reload_strategy':
                const reloadRes = await axios.post(`${FREQTRADE_API_URL}/reload_config`, {}, { auth: AUTH });
                return { content: [{ type: 'text', text: 'Estrategia recargada con éxito: ' + JSON.stringify(reloadRes.data) }] };

            case 'balance':
                const balanceRes = await axios.get(`${FREQTRADE_API_URL}/balance`, { auth: AUTH });
                return { content: [{ type: 'text', text: JSON.stringify(balanceRes.data, null, 2) }] };

            default:
                return {
                    content: [{ type: 'text', text: `Acción desconocida: ${action}. Acciones disponibles: status, profit, daily, reload_strategy, balance` }],
                    isError: true
                };
        }
    } catch (error: any) {
        return {
            content: [{ type: 'text', text: `Error al conectar con Freqtrade: ${error.message}. Asegúrate de que el bot esté corriendo en el puerto 8080.` }],
            isError: true
        };
    }
}
