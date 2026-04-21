import requests

token = "7998240806:AAHDUkFw6quDuoFB_fs5Altv8g9M_zP9-XU"
chat_id = "6527908321"
message = "🦅 [AUDITORÍA]: Prueba de conexión desde el laboratorio Chacal. ¿Me recibes?"

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {"chat_id": chat_id, "text": message}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
