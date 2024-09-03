#%%
import os
import json
import pprint
import random
import requests
import cloudscraper
from bs4 import BeautifulSoup

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
    
    def extractor(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        datatable = {}
        twincn =  {}

        # table_selectors = [
        #     'table.table.table-striped#basic-data',   # 1. <table class="table table-striped" id="basic-data">
        #     'table.table.table-striped:not([id])',    # 2. <table class="table table-striped">（無id）
        #     'table.table.table-striped ' ]

        # for idx, selector in enumerate(table_selectors, start=1):
        #     tables = soup.select(selector)
        #     for table in tables:
        #         table_id = f"table_{idx:02}"
        #         table_text = table.get_text(separator=' ', strip=True)
        #         datatable[table_id] = table_text
            
        # tables_json = json.dumps(datatable, ensure_ascii=False, indent=4)

        table_count = 1  # 用來計算表格數量

        # 查找所有符合條件的table標籤
        table_selectors = [
            'table.table.table-striped#basic-data',   # 1. <table class="table table-striped" id="basic-data">
            'table.table.table-striped:not([id])',    # 2. <table class="table table-striped">（無id）
            #'table.table.table-striped '              # 3. <table class="table table-striped "> (有空格)
        ]

        # 遍歷每個選擇器，提取對應表格內容
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
#%%
if __name__ == "__main__":
    crawler = Scraper()
    taxid = "24716716"
    res, searchurl = crawler.crawltwincn(taxid=taxid)
    datatable = crawler.extractor(content=res)
    pprint.pprint(datatable)
#%%