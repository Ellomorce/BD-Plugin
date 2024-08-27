import requests
import json

url = "http://127.0.0.1:9001/bdginie"
headers = {'Content-Type': 'text/plain'}
data = "{\"message\": \"請幫助我分析台達電子股份有限公司這家公司有沒有貸款、保險或銷售股票的需求。\"}"

response = requests.post(url, headers=headers, data=data)
print(response.json())

# raw = {"message": "請幫助我分析台達電子股份有限公司這家公司有沒有貸款、保險或銷售股票的需求。"}
# dump = json.dumps(raw, ensure_ascii=False)
# print(dump)

# test = "{\"message\": \"請幫助我分析台達電子股份有限公司這家公司有沒有貸款、保險或銷售股票的需求。\"}"
# res = json.loads(test)
# print(res)
# print(res.get("message"))
