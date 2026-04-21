import requests

token = "8760247299:AAHNhw7k-YlEG2kL7lO0Ze5cbuRzg7y8bW4"
chat_id = "6527908321"
message = "🦅 [AWS SNIPER-CORE]: ¡SISTEMA RESTABLECIDO! Auditoría de AWS completada. Bozales eliminados. ¿Recibes este aviso en el canal correcto?"

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {"chat_id": chat_id, "text": message}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
