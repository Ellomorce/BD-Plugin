##################################
# Author : Shaun Hsieh
# Edit Time: 2024/08/15
# Github Repo：BD-Plugin
##################################
FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

ENV SYSTEMBID="你是一個精準的關鍵詞偵測器，你能從使用者的問題中擷取出公司名稱，並簡短的返回公司名稱，除了公司名稱外你不會返回任何其他的內容。\ 
Instructions:\
- 請以JSON格式回覆: {'company_name': '公司名稱'}"

EXPOSE 9001

# CMD ["gunicorn", "bdginie:app", "--host", "0.0.0.0", "--port", "9001"]
CMD ["gunicorn", "bdginie:app", "--bind", "0.0.0.0:9001", "--timeout", "600"]