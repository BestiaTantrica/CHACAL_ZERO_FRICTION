import requests

token = "8750236428:AAGpdMa-GsgJ3LyagAQAM_UUzsKCFWZTE_4"
chat_id = "6527908321"
message = "🦅 [CEREBRO CHACAL]: ¡CONEXIÓN ESTABLECIDA! Auditando el sistema Trifásico... ¿Me copias, Capitán?"

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {"chat_id": chat_id, "text": message}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
