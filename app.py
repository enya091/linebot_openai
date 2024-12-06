from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import openai
import traceback

# 初始化 Flask 應用
app = Flask(__name__)

# LineBot 配置
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY')

# 紀錄使用者的回覆內容
user_data = {}

def GPT_recommendation(drink, mood, taste):
    """
    統整使用者的回覆，並使用 OpenAI GPT 生成推薦調酒
    """
    prompt = f"""
    根據以下需求，推薦一款適合的調酒，並簡要說明原因：
    1. 想喝的酒種類：{drink}
    2. 今天的心情：{mood}
    3. 偏好的口味：{taste}
    請提供調酒名稱和解釋原因。
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    return response['choices'][0]['message']['content']

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(FollowEvent)  # 當使用者第一次加入時觸發
def welcome_message(event):
    user_id = event.source.user_id
    if user_id not in user_data:
        user_data[user_id] = {"drink": None, "mood": None, "taste": None}
    
    welcome_text = "哈囉！歡迎光臨 xx 調酒店！✨\n接下來讓我們為你挑選一款適合的調酒！"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(welcome_text))
    
    # 發送第一個問題
    buttons_template = TemplateSendMessage(
        alt_text='選擇酒類',
        template=ButtonsTemplate(
            title='今天想喝什麼酒？',
            text='選擇一種酒類',
            actions=[
                PostbackAction(label='威士忌', data='drink=威士忌'),
                PostbackAction(label='伏特加', data='drink=伏特加'),
                PostbackAction(label='龍舌蘭', data='drink=龍舌蘭'),
                PostbackAction(label='蘭姆酒', data='drink=蘭姆酒')
            ]
        )
    )
    line_bot_api.push_message(user_id, buttons_template)

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    data = event.postback.data
    
    if user_id not in user_data:
        user_data[user_id] = {"drink": None, "mood": None, "taste": None}
    
    # 儲存使用者的回覆
    if data.startswith("drink="):
        user_data[user_id]["drink"] = data.split("=")[1]
        # 問下一個問題：心情
        buttons_template = TemplateSendMessage(
            alt_text='選擇心情',
            template=ButtonsTemplate(
                title='今天心情如何？',
                text='選擇你的心情',
                actions=[
                    PostbackAction(label='開心', data='mood=開心'),
                    PostbackAction(label='放鬆', data='mood=放鬆'),
                    PostbackAction(label='平靜', data='mood=平靜'),
                    PostbackAction(label='需要鼓勵', data='mood=需要鼓勵')
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    
    elif data.startswith("mood="):
        user_data[user_id]["mood"] = data.split("=")[1]
        # 問下一個問題：口味
        buttons_template = TemplateSendMessage(
            alt_text='選擇口味',
            template=ButtonsTemplate(
                title='現在比較想吃什麼？',
                text='選擇對應的口味',
                actions=[
                    PostbackAction(label='檸檬（酸）', data='taste=酸'),
                    PostbackAction(label='糖果（甜）', data='taste=甜'),
                    PostbackAction(label='咖啡（苦）', data='taste=苦'),
                    PostbackAction(label='辣椒（辣）', data='taste=辣')
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    
    elif data.startswith("taste="):
        user_data[user_id]["taste"] = data.split("=")[1]
        # 呼叫 GPT 生成推薦調酒
        drink = user_data[user_id]["drink"]
        mood = user_data[user_id]["mood"]
        taste = user_data[user_id]["taste"]
        recommendation = GPT_recommendation(drink, mood, taste)
        
        # 回覆推薦調酒
        line_bot_api.reply_message(event.reply_token, TextSendMessage(recommendation))
        
        # 清空使用者資料
        user_data[user_id] = {"drink": None, "mood": None, "taste": None}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
