#%%
import os
import json
import random
import requests
import yaml
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
                 model, 
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
        self.modelname = model
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
        elif prompt_type == "detector":
            system = """你是一個精準的關鍵詞偵測器，你能從使用者的問題中擷取出公司名稱，並簡短的返回公司名稱，除了公司名稱外你不會返回任何其他的內容。
            Instructions: 
            - 請以JSON格式回覆: {"company_name": "公司名稱"}"""
            user = content
        else:
            with open('Inputs.yaml', 'r') as file:
                prompt = yaml.load(file, Loader=yaml.FullLoader)['prompt']
                system = prompt["system"]
                user = content
        return system, user
    
    def generate(self, system, user, response_type):
        if response_type == None:
            response_type == "chat"
        message = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if user == "":
            return "Content is invalid."
        elif user == None:
            return "Content is invalid."
        else:
            if response_type == "chat":
                try:
                    response = self.client.chat.completions.create(
                        messages= message,
                        model= self.modelname,
                        max_tokens=self.max_new_tokens,
                        frequency_penalty= self.frequency_penalty,
                        temperature= self.temperature,
                        top_p= self.top_p
                    )
                    return response.choices[0].message.content
                except Exception as errmsg:
                    return errmsg
            elif response_type == "detector":
                try:
                    response = self.client.chat.completions.create(
                        messages= message,
                        model= self.modelname,
                        response_format={ "type": "json_object" },
                        max_tokens=self.max_new_tokens,
                        frequency_penalty= self.frequency_penalty,
                        temperature= self.temperature,
                        top_p= self.top_p
                    )
                    return response.choices[0].message.content
                except Exception as errmsg:
                    return errmsg

if __name__=='__main__':
    load_dotenv("../bdginie/project.env")
    bingkey = os.getenv("BINGKEY")
    azure_endpoint = os.getenv("AZURE_ENDPOINT")
    azure_apiversion = os.getenv("AZURE_APIVERSION")
    azure_apikey = os.getenv("AZURE_APIKEY")
    azure_deployment = os.getenv("AZURE_DEPLOYMENT")
    azure_modelname = os.getenv("AZURE_MODELNAME")
    with open('Inputs.yaml', 'r') as file:
        user_query = yaml.load(file, Loader=yaml.FullLoader)['user_query']
    crawler = scraper()
    llm = AOAI(endpoint=azure_endpoint,
                   apiversion=azure_apiversion,
                   apikey=azure_apikey,
                   deployment=azure_deployment,
                   model=azure_modelname,
                   maxtoken=2048,
                   temp=0.5,
                   topk=0.5,
                   topp=0.5,
                   fpenalty=1.0)
#%%
    system_bid, user_bid = llm.select_prompt(prompt_type="detector", content=user_query)
    res = llm.generate(system=system_bid, user=user_query, response_type="detector")
    comp_res = json.loads(res)
    if "company_name" in comp_res.keys():
        comp_name = comp_res["company_name"]
    else:
        comp_name = str(comp_res)
    print(comp_name)
#%%
    # 輸入查詢公司名稱
    try:
        if comp_name:
            keyword=comp_name
    except: 
        keyword = input()
    data104 = crawler.crawl104(keyword=keyword)
    search_term = f"{keyword}主要營業項目經營團隊競爭優勢進貨廠商銷售市場貸款需求"
    bing_results = crawler.search_bing(subscription_key=bingkey, search_term=search_term)
    bddata = [data104]
    bddata.extend(bing_results)
    with open(f"{keyword}.json", "w", encoding='utf-8-sig') as outfile:
            json.dump(bddata, outfile, ensure_ascii=False)
#%%
    # Getting BID
    # bid_term = f"{keyword}統一編號"
    # bid_results = crawler.search_bing(subscription_key=bingkey, search_term=bid_term)
    # print(bid_results)
#%%
    test_json = ""
    with open(test_json, "r", encoding='utf-8-sig') as file:
        bd_ref = json.load(file)
    content_front = "以下文件內容是有關目標公司的JSON資料，請參考這些資料，幫助使用者分析目標公司所在的市場、主要經營項目、負責人、經營團隊，並進一步分析是否有銀行貸款、團體保險、尋找股票銷售代理商的需求。以下是有關目標公司的資料:\r\n"
    content = content_front + str(bd_ref)
    system, user = llm.select_prompt(prompt_type="else", content=bd_ref)
    bd_res = llm.generate(system=system_bid, user=user_query, response_type="chat")
    print(bd_res)
#%%