import json

import requests

url = "https://api.close.com/buildwithus/"
response = requests.get(url)

print(response.status_code)
print(json.dumps(response.json(), indent=2))
