import os
import json
import random
import re
import requests
import cloudscraper
import uvicorn
# from dotenv import load_dotenv
from urllib.parse import urlencode
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AzureOpenAI
from bs4 import BeautifulSoup

app = FastAPI()

# Banned CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許任何來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load_dotenv("project.env")
bingkey = os.getenv("BINGKEY")
azure_endpoint = os.getenv("AZURE_ENDPOINT")
azure_apiversion = os.getenv("AZURE_APIVERSION")
azure_apikey = os.getenv("AZURE_APIKEY")
azure_deployment = os.getenv("AZURE_DEPLOYMENT")
azure_modelname = os.getenv("AZURE_MODELNAME")
system_bid = os.getenv("SYSTEMBID")
# system_bid = "你是一個精準的關鍵詞偵測器，你能從使用者的問題中擷取出公司名稱，並簡短的返回公司名稱，除了公司名稱外你不會返回任何其他的內容。\
#     Instructions:\
#         - 請以JSON格式回覆: {'company_name': '公司名稱'}"

# class QueryRequest(BaseModel):
#     message: str

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
        print("Bing Search Reponse Check:", response.text)
        search_results = response.json()['webPages']['value'] 
        bing_results = []
        for result in search_results:
            name = result.get('name')
            url = result.get('url')
            snippet = result.get('snippet')
            bing_results.append({'name':name, 'url':url, 'snippet':snippet})
        return bing_results
    
    def bid_extractor(self, bing_results):
        bid = {"統一編號": "notaxids"}
        infourl = None
        for info in bing_results:
            if "台灣公司網" in info['name']:
                print("台灣公司網")
                if "統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "公司統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"公司統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號為 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號為 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                #
                elif "統一編號 (統編):" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (統編):(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "營利事業統一編號是 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"營利事業統一編號是 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                else:
                    pass
            elif "台灣公司情報網" in info['name']:
                print("台灣公司情報網")
                if "統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "公司統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"公司統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號為 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號為 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                #
                elif "統一編號 (統編):" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (統編):(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "營利事業統一編號是 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"營利事業統一編號是 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                else:
                    pass
            elif "公司登記查詢中心" in info['name']:
                print("公司登記查詢中心")
                if "統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "公司統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"公司統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號為 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號為 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                #
                elif "統一編號 (統編):" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (統編):(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "營利事業統一編號是 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"營利事業統一編號是 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                else:
                    pass
            elif "開放政府臺灣資料" in info['name']:
                print("開放政府臺灣資料")
                if "統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "公司統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"公司統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號為 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號為 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                #
                elif "統一編號 (統編):" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (統編):(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "營利事業統一編號是 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"營利事業統一編號是 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                else:
                    pass
            elif "臺灣政府開放資料平台" in info['name']:
                print("臺灣政府開放資料平台")
                if "統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "公司統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"公司統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號為 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號為 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                #
                elif "統一編號 (統編):" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (統編):(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "營利事業統一編號是 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"營利事業統一編號是 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                else:
                    pass
            elif "全國前500大公司資料集" in info['name']:
                print("全國前500大公司資料集")
                if "統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "公司統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"公司統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號為 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號為 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                #
                elif "統一編號 (統編):" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (統編):(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "營利事業統一編號是 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"營利事業統一編號是 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                else:
                    pass
            elif "上市公司基本資料" in info['name']:
                print("上市公司基本資料")
                if "統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "公司統編:" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"公司統編:(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號為 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號為 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                #
                elif "統一編號 (統編):" in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (統編):(\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "營利事業統一編號是 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"營利事業統一編號是 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                elif "統一編號 " in info['snippet'].replace("\ue001", "").replace("\ue000", ""):
                    text = info['snippet'].replace("\ue001", "").replace("\ue000", "")
                    infourl = info['url']
                    match = re.search(r"統一編號 (\d{8})", text)
                    bid_str = match.group(1)
                    bid["統一編號"] = bid_str
                    break
                else:
                    pass
            else:
                continue
        if infourl == None:
            infourl = "Company Url Not Found."
        return bid, infourl

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
    
    def crawltwincn(self, taxid):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd", 
            "Accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "authority": "www.twincn.com",
            "User-Agent": self.user_agent[random.randint(0, len(self.user_agent)-1)],
            }
        searchurl = f"https://www.twincn.com/item.aspx?no={taxid}"
        raw = self.scraper.get(url=searchurl, headers=headers)
        decoded_content = raw.content.decode('utf-8')
        return decoded_content, searchurl
    
    def extractor(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        datatable = {}
        twincn =  {}
        table_count = 1  # 用來計算表格數量
        table_selectors = [
            'table.table.table-striped#basic-data',   # 1. <table class="table table-striped" id="basic-data">
            'table.table.table-striped:not([id])',    # 2. <table class="table table-striped">（無id）
            #'table.table.table-striped '              # 3. <table class="table table-striped "> (有空格)
        ]
        for selector in table_selectors:
            tables = soup.select(selector)
            for table in tables:
                table_id = f"table_{table_count:02}"  # 根據總表格數來編號
                # 提取表格中的所有文字
                table_text = table.get_text(separator=' ', strip=True)
                # 儲存在字典中
                datatable[table_id] = table_text
                table_count += 1
        
        twincn["basic data"] = datatable["table_01"]
        
        for k, v in datatable.items():
            if "代表法人" in v:
                twincn["shareholder"]=datatable[k]
            elif "法院案號" in v:
                twincn["judgment history"]=datatable[k]
            elif "工廠編號" in v:
                twincn["factories"]=datatable[k]
            elif "到職日" in v:
                twincn["managers"]=datatable[k]
        return twincn
    
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
    
    def generate(self, system, user, response_type=None):
        if response_type is None:
            response_type = "chat"
        message = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if not user:
            return "Content is invalid."
        else:
            try:
                if response_type == "chat":
                    response = self.client.chat.completions.create(
                        messages=message,
                        model=self.modelname,
                        max_tokens=self.max_new_tokens,
                        frequency_penalty=self.frequency_penalty,
                        temperature=self.temperature,
                        top_p=self.top_p
                    )
                    print("GPT Reponse Check:", response)
                    return response.choices[0].message.content
                elif response_type == "detector":
                    response = self.client.chat.completions.create(
                        messages=message,
                        model=self.modelname,
                        response_format={"type": "json_object"},
                        max_tokens=self.max_new_tokens,
                        frequency_penalty=self.frequency_penalty,
                        temperature=self.temperature,
                        top_p=self.top_p
                    )
                    print("GPT Reponse Check:", response)
                    return response.choices[0].message.content
            except Exception as errmsg:
                return str(errmsg)

@app.post("/bdginie")
async def run_bdginie(request: Request):
    try:
        raw_data = await request.body()
        # print("Raw Data is:", raw_data)
        json_str = raw_data.decode("utf-8")
        # print("Received JSON String:", json_str)  # 調試用
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)
            raise HTTPException(status_code=400, detail="Invalid JSON string.")
        
        if isinstance(data, str):
            query_data = eval(data)
        else:
            query_data = data
        user_query = query_data.get('message')
        if not user_query:
            raise HTTPException(status_code=400, detail="Message field is required.")
        # 
        crawler = Scraper()
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
        #
        system_bid = """你是一個精準的關鍵詞偵測器，你能從使用者的問題中擷取出公司名稱，並簡短的返回公司名稱，除了公司名稱外你不會返回任何其他的內容。
        Instructions:
        - 請以JSON格式回覆: {'company_name': '公司名稱'}"""
        res = llm.generate(system=system_bid, user=user_query, response_type="detector")
        comp_res = json.loads(res)
        # 從使用者對話擷取公司名稱
        if "company_name" in comp_res.keys():
            if len(comp_res["company_name"]) == 0:
                comp_name = "corpname_missing"
                bid = "Extract Company Name Failed"
            else:
                comp_name = comp_res["company_name"]
                # 搜尋統一編號
                bid_term = f"{comp_name}統一編號負責人資本額地址電話"
                bid_results = crawler.search_bing(subscription_key=bingkey, search_term=bid_term)
                bid, infourl = crawler.bid_extractor(bing_results=bid_results)
        else:
            comp_name = str(comp_res)
            # 搜尋統一編號
            bid_term = f"{comp_name}統一編號負責人資本額地址電話"
            bid_results = crawler.search_bing(subscription_key=bingkey, search_term=bid_term)
            bid, infourl = crawler.bid_extractor(bing_results=bid_results) # bid is a dict
        #
        taxid = bid["統一編號"]
        if taxid == "notaxids":
            corpdata = "使用者輸入的內容可能不含公司名稱或名稱錯誤，未查詢到該公司相關資料"
            twincnurl = "使用者輸入的內容可能不含公司名稱或名稱錯誤，未查詢到該公司相關網址"
        else:
            twincn_data, searchurl = crawler.crawltwincn(taxid=taxid)
            corpdata = crawler.extractor(content=twincn_data) # dict
            twincnurl = {"台灣公司網公司資料連結": searchurl} # dict
        #
        if comp_name == "corpname_missing":
            data104 = ["104人力銀行網站上沒有目標公司的資料"]
        else:
            data104 = crawler.crawl104(keyword=comp_name)
            search_term = f"{comp_name}主要客戶產品優勢產業分析研究報告"
            bing_results = crawler.search_bing(subscription_key=bingkey, search_term=search_term)
        #
        bddata = [bid]
        bddata.append(twincnurl)
        bddata.append(corpdata)
        bddata.append(data104)
        bddata.extend(bing_results)
        return {"result": bddata}
    
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9001)
