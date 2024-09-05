#%%
import os
import re
import requests
import json
import pprint
from dotenv import load_dotenv
load_dotenv("project.env")
bingkey = os.getenv("BINGKEY")

def search_bing(subscription_key, search_term):
    bingurl = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {
        "q": search_term,
        "mkt": 'zh-TW',
        "textDecorations": True,
    }
    response = requests.get(bingurl, headers=headers, params=params)
    response.raise_for_status()
    print("Bing Search Reponse Check:", response.text)
    search_results = response.json()['webPages']['value'] 
    bing_results = []
    for result in search_results:
        name = result.get('name')
        url = result.get('url')
        snippet = result.get('snippet')
        bing_results.append({'name':name, 'url':url, 'snippet':snippet})
    return bing_results
#%%
comp_name = "京元電子"
bid_term = f"{comp_name}統一編號負責人資本額地址電話"
bid_results = search_bing(subscription_key=bingkey, search_term=bid_term)
#%%
pprint.pprint(bid_results)
#%%
x = bid_results[2]['snippet'].replace("\ue001", "").replace("\ue000", "")
print(x)
#%%