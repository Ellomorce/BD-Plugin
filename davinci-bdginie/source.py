import json
import asyncio
from pyodide.http import pyfetch

async def post_data():
    try:
        response = await pyfetch(
            'https://127.0.0.1/yourapi',
            method='POST',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body=json.dumps({
                "message": str(CURRENT_CONVERSATION[-1]["content"])
            })
        )
        if response.status == 200:
            data = await response.json()  # 假設回應是 JSON 格式
            print(data)
        else:
            print("Error:", response.status)
    except Exception as e:
        print("An error occurred:", e)

# 使用 asyncio 運行
await post_data()