import os
import json
import random
import requests
import cloudscraper
from urllib.parse import urlencode
from dotenv import load_dotenv
from openai import AzureOpenAI

class scraper:
    
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
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1', 'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363']
        self.bingurl = "https://api.bing.microsoft.com/v7.0/search"

    def search_bing(self, subscription_key, search_term):
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
        params = {
            "q": search_term,
            # "freshness": 'Month', 先不設定
            "mkt": 'zh-TW',
            "textDecorations": True,
            }
        response = requests.get(self.bingurl, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()['webPages']['value'] 
        #only get name, url and snippet
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
        if embed == None:
            pass
        else:
            self.embed = embed
        self.max_new_tokens = maxtoken
        self.temperature = temp
        self.top_k = topk
        self.top_p = topp
        self.frequency_penalty = fpenalty
        self.client = AzureOpenAI(
            azure_endpoint= self.endpoint,
            api_key= self.api_key,
            api_version= self.api_version,
            azure_deployment= self.deployment,
            default_headers= {"conten-type": "application/json"}
        )

    def select_prompt(self, prompt_type, prompt=None, content=None, template=None):
        if prompt_type == 'test':
            system = "You are professional translator, you can translate english to traditional chinese."
            user = "Shaun is a reliable engineer."
            assistant = ""
        elif prompt_type == "bid":
            system = "你是一個精準的關鍵詞偵測器，你能從使用者的問題中擷取出公司名稱，並簡短的返回公司名稱，除了公司名稱外你不會返回任何其他的內容。"
            user = content
            assistant = """{"company_name": "公司名稱"}"""
        else:
            system = prompt
            user = content
            assistant = template
        return system, user, assistant
    
    def generate(self, system, user, assistant, reponse_type=None):
        if reponse_type == None:
            reponse_type == "chat"
        message = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant}
        ]
        if user == "":
            return "Content is invalid."
        elif user == None:
            return "Content is invalid."
        else:
            if reponse_type == "chat":
                try:
                    response = self.client.chat.completions.create(
                        messages= message,
                        modelname= self.modelname,
                        max_tokens=self.max_new_tokens,
                        frequency_penalty= self.frequency_penalty,
                        temperature= self.temperature,
                        top_p= self.top_p
                    )
                    return response.choices[0].message.content
                except Exception as errmsg:
                    return errmsg
            elif reponse_type == "detector":
                try:
                    response = self.client.chat.completions.create(
                        messages= message,
                        modelname= self.modelname,
                        response_format={ "type": "json_object" },
                        max_tokens=self.max_new_tokens,
                        frequency_penalty= self.frequency_penalty,
                        temperature= self.temperature,
                        top_p= self.top_p
                    )
                    return response.choices[0].message.content
                except Exception as errmsg:
                    return errmsg
# This Sector Needs User Passing from api calling
keyword=""
user_query =""
#
# This Sector are other api keys need to be load from .env or dockerfile
load_dotenv("project.env") 
bingkey = os.getenv("BINGKEY")
#
crawler = scraper()
data104 = crawler.crawl104(keyword=keyword)
search_term = f"{user_query}主要營業項目經營團隊競爭優勢進貨廠商銷售市場貸款需求"
bing_results = crawler.search_bing(subscription_key=bingkey, search_term=search_term)
bddata = [data104]
bddata.extend(bing_results)