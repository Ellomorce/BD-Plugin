#%%
import re
import requests
import json
import pprint

url = "http://127.0.0.1:9001/bdginie"
headers = {'Content-Type': 'text/plain'}
data = "{\"message\": \"請幫助我分析台達電子股份有限公司這家公司有沒有貸款、保險或銷售股票的需求。\"}"
#%%
response = requests.post(url, headers=headers, data=data)
pprint.pprint(response.json())
#%%
# raw = {"message": "請幫助我分析台達電子股份有限公司這家公司有沒有貸款、保險或銷售股票的需求。"}
# dump = json.dumps(raw, ensure_ascii=False)
# print(dump)

# test = "{\"message\": \"請幫助我分析台達電子股份有限公司這家公司有沒有貸款、保險或銷售股票的需求。\"}"
# res = json.loads(test)
# print(res)
# print(res.get("message"))
#%%
res = response.json()['result']
for website in res:
    if "台灣公司網" in website['name']:
        txtbag = website['snippet']
    else:
        pass
pprint.pprint(txtbag)
#%%
match = re.search(r"統編:(\d{8})", txtbag)
print(match.group(1))
#%%