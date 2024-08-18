import os
import json
import random
import requests
import cloudscraper
import uvicorn
from urllib.parse import urlencode
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AzureOpenAI

app = FastAPI()
bingkey = os.getenv("BINGKEY")
azure_endpoint = os.getenv("AZURE_ENDPOINT")
azure_apiversion = os.getenv("AZURE_APIVERSION")
azure_apikey = os.getenv("AZURE_APIKEY")
azure_deployment = os.getenv("AZURE_DEPLOYMENT")
azure_modelname = os.getenv("AZURE_MODELNAME")
system = os.getenv("SYSTEM")
assistant = os.getenv("ASSISTANT")

class QueryRequest(BaseModel):
    user_query: str

class Scraper:
    
    def __init__(self) -> None:
        self.sess = requests.session()
        self.scraper = cloudscraper.create_scraper(sess=self.sess, disableCloudflareV1=True, debug=False, 
                                                   browser={
                                                       'browser': 'chrome',
                                                       'platform': 'android',
                                                       'desktop': False}
                                                       )
        self.user_agent = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1', 
                'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363']
        self.bingurl = "https://api.bing.microsoft.com/v7.0/search"

    def search_bing(self, subscription_key, search_term):
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
        params = {
            "q": search_term,
            "mkt": 'zh-TW',
            "textDecorations": True,
        }
        response = requests.get(self.bingurl, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()['webPages']['value'] 
        bing_results = []
        for result in search_results:
            name = result.get('name')
            url = result.get('url')
            snippet = result.get('snippet')
            bing_results.append({'name':name, 'url':url, 'snippet':snippet})
        return bing_results

    def crawl104(self, keyword):
        keyword_urlcode = urlencode([("keyword", f"{keyword}")])
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd", 
            "Accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "connection": "keep-alive", 
            "Host": "www.104.com.tw",
            "Referer": f"https://www.104.com.tw/company/search/?jobsource=cs_n104bank2&{keyword_urlcode}",
            "User-Agent": self.user_agent[random.randint(0, len(self.user_agent)-1)],
            }
        searchurl = f"https://www.104.com.tw/company/ajax/list?jobsource=cs_n104bank2&{keyword_urlcode}"
        searchlist = self.scraper.get(url=searchurl, headers=headers)
        decoded_content = searchlist.content.decode('utf-8')
        data = json.loads(decoded_content)
        return data["data"][0]
    
class AOAI:

    def __init__(self, 
                 endpoint, 
                 apiversion, 
                 apikey, 
                 deployment, 
                 modelname, 
                 maxtoken, 
                 temp, 
                 topk, 
                 topp, 
                 fpenalty, 
                 embed=None) -> None:
        
        self.apitype = "azure"
        self.endpoint = endpoint
        self.api_version = apiversion
        self.api_key = apikey
        self.deployment = deployment
        self.modelname = modelname
        if embed is not None:
            self.embed = embed
        self.max_new_tokens = maxtoken
        self.temperature = temp
        self.top_k = topk
        self.top_p = topp
        self.frequency_penalty = fpenalty
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            azure_deployment=self.deployment,
            default_headers={"content-type": "application/json"}
        )
    
    def generate(self, system, user, assistant, response_type=None):
        if response_type is None:
            response_type = "chat"
        message = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant}
        ]
        if not user:
            return "Content is invalid."
        else:
            try:
                if response_type == "chat":
                    response = self.client.chat.completions.create(
                        messages=message,
                        modelname=self.modelname,
                        max_tokens=self.max_new_tokens,
                        frequency_penalty=self.frequency_penalty,
                        temperature=self.temperature,
                        top_p=self.top_p
                    )
                    return response.choices[0].message.content
                elif response_type == "detector":
                    response = self.client.chat.completions.create(
                        messages=message,
                        modelname=self.modelname,
                        response_format={"type": "json_object"},
                        max_tokens=self.max_new_tokens,
                        frequency_penalty=self.frequency_penalty,
                        temperature=self.temperature,
                        top_p=self.top_p
                    )
                    return response.choices[0].message.content
            except Exception as errmsg:
                return str(errmsg)

@app.post("/bdginie")
def run_bdginie(query: QueryRequest):
    try:
        user_query = query.user_query
        #
        crawler = Scraper()
        llm = AOAI(endpoint=azure_endpoint,
                   apiversion=azure_apiversion,
                   apikey=azure_apikey,
                   deployment=azure_deployment,
                   modelname=azure_modelname,
                   maxtoken=2048,
                   temp=0.5,
                   topk=0.5,
                   topp=0.5,
                   fpenalty=1.0)
        #
        res = llm.generate(system=system, user=user_query, assistant=assistant, response_type="detector")
        comp_res = json.loads(res)
        if "company_name" in comp_res.keys():
            comp_name = comp_res["company_name"]
        else:
            comp_name = str(comp_res)
        data104 = crawler.crawl104(keyword=comp_name)
        # 搜尋統一編號來查詢金腦資料，目前暫時用不到，先註解掉，如果之後要用記得bing回傳的東西需要再解析
        # bid_term = f"{user_query}統一編號"
        # bid_results = crawler.search_bing(subscription_key=bingkey, search_term=bid_term)
        #
        search_term = f"{user_query}主要營業項目經營團隊競爭優勢進貨廠商銷售市場貸款需求保險需求"
        bing_results = crawler.search_bing(subscription_key=bingkey, search_term=search_term)
        #
        bddata = [data104]
        bddata.extend(bing_results)
        return {"result": bddata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 測試路由
@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9001)