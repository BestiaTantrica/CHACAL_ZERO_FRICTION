import json

with open('c:/CHACAL_ZERO_FRICTION/scripts/config_aws.json', 'r') as f:
    data = json.load(f)
    token = data['telegram']['token']
    print(f"Token: '{token}'")
    print(f"Hex: {token.encode('utf-8').hex()}")
