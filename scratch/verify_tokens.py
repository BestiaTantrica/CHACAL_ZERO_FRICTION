import requests

tokens = [
    "7998240806:AAHDUkFw6quDuoFB_fs5Altv8g9M_zP9-XU",
    "8750236428:AAGpdMa-GsgJ3LyagAQAM_UUzsKCFWZTE_4",
    "8760247299:AAHNhw7k-YlEG2kL7lO0Ze5cbuRzg7y8bW4"
]

for token in tokens:
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        print(f"Token: {token}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
