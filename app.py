from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackAction, TextSendMessage
import os
import openai
import traceback

app = Flask(__name__)

# Channel Access Token 和 Secret
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY')

# 紀錄使用者的回覆
user_data = {}

def GPT_recommendation(drink, mood, taste, occasion, weather):
    """
    使用 OpenAI GPT 生成調酒推薦
    """
    prompt = f"""
    你是一名專業的調酒師。根據以下使用者提供的信息，推薦一款適合的調酒，並簡要說明原因：
    1. 今天想喝的酒類：{drink}
    2. 今天的心情：{mood}
    3. 偏好的口味：{taste}
    4. 場合：{occasion}
    5. 天氣：{weather}

    請提供調酒名稱和解釋原因。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a professional bartender."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        app.logger.error(f"GPT API Error: {e}")
        return "抱歉，目前無法為您推薦調酒，請稍後再試！"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info(f"Webhook received: {body}")  # 紀錄 Webhook 請求
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature error")
        abort(400)
    return 'OK'


@handler.add(FollowEvent)
def welcome_message(event):
    """
    當使用者第一次加入時，發送歡迎訊息並問第一個問題
    """
    user_id = event.source.user_id
    if user_id not in user_data:
        user_data[user_id] = {"drink": None, "mood": None, "taste": None, "occasion": None, "weather": None}

    welcome_text = "哈囉！歡迎光臨 xx 調酒店！✨\n接下來讓我們為你挑選一款適合的調酒！"
    try:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(welcome_text))
        app.logger.info("Welcome message sent successfully")
    except Exception as e:
        app.logger.error(f"Error sending welcome message: {e}")

    # 問第一個問題
    ask_drink(event, user_id)

def ask_drink(event, user_id):
    """
    問第一個問題：今天想喝什麼酒？
    """
    app.logger.info(f"Asking drink question for user: {user_id}")  # 確保函數被執行
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
    try:
        line_bot_api.push_message(user_id, buttons_template)
        app.logger.info("Drink question sent successfully")
    except Exception as e:
        app.logger.error(f"Error sending drink question: {e}")  # 錯誤日誌

def ask_mood(event, user_id):
    """
    問第二個問題：今天心情如何？
    """
    app.logger.info(f"Asking mood question for user: {user_id}")
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
    try:
        line_bot_api.push_message(user_id, buttons_template)
        app.logger.info("Mood question sent successfully")
    except Exception as e:
        app.logger.error(f"Error sending mood question: {e}")

def ask_taste(event, user_id):
    """
    問第三個問題：現在比較想吃什麼？
    """
    app.logger.info(f"Asking taste question for user: {user_id}")
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
    try:
        line_bot_api.push_message(user_id, buttons_template)
        app.logger.info("Taste question sent successfully")
    except Exception as e:
        app.logger.error(f"Error sending taste question: {e}")

def ask_occasion(event, user_id):
    """
    問第四個問題：今天是什麼場合？
    """
    app.logger.info(f"Asking occasion question for user: {user_id}")
    buttons_template = TemplateSendMessage(
        alt_text='選擇場合',
        template=ButtonsTemplate(
            title='今天是什麼場合？',
            text='選擇場合',
            actions=[
                PostbackAction(label='聚會', data='occasion=聚會'),
                PostbackAction(label='約會', data='occasion=約會'),
                PostbackAction(label='放鬆', data='occasion=放鬆'),
                PostbackAction(label='工作', data='occasion=工作')
            ]
        )
    )
    try:
        line_bot_api.push_message(user_id, buttons_template)
        app.logger.info("Occasion question sent successfully")
    except Exception as e:
        app.logger.error(f"Error sending occasion question: {e}")

def ask_weather(event, user_id):
    """
    問第五個問題：今天的天氣如何？
    """
    app.logger.info(f"Asking weather question for user: {user_id}")
    buttons_template = TemplateSendMessage(
        alt_text='選擇天氣',
        template=ButtonsTemplate(
            title='今天的天氣如何？',
            text='選擇天氣狀況',
            actions=[
                PostbackAction(label='晴天', data='weather=晴天'),
                PostbackAction(label='陰天', data='weather=陰天'),
                PostbackAction(label='雨天', data='weather=雨天'),
                PostbackAction(label='寒冷', data='weather=寒冷')
            ]
        )
    )
    try:
        line_bot_api.push_message(user_id, buttons_template)
        app.logger.info("Weather question sent successfully")
    except Exception as e:
        app.logger.error(f"Error sending weather question: {e}")

@handler.add(PostbackEvent)
def handle_postback(event):
    """
    處理使用者的回覆並進入下一步問題
    """
    user_id = event.source.user_id
    data = event.postback.data
    app.logger.info(f"PostbackEvent triggered for user: {user_id}, data: {data}")  # 確保按鈕事件有觸發

    if user_id not in user_data:
        user_data[user_id] = {"drink": None, "mood": None, "taste": None, "occasion": None, "weather": None}

    # 儲存回覆
    if data.startswith("drink="):
        user_data[user_id]["drink"] = data.split("=")[1]
        ask_mood(event, user_id)

    elif data.startswith("mood="):
        user_data[user_id]["mood"] = data.split("=")[1]
        ask_taste(event, user_id)

    elif data.startswith("taste="):
        user_data[user_id]["taste"] = data.split("=")[1]
        ask_occasion(event, user_id)

    elif data.startswith("occasion="):
        user_data[user_id]["occasion"] = data.split("=")[1]
        ask_weather(event, user_id)

    elif data.startswith("weather="):
        user_data[user_id]["weather"] = data.split("=")[1]
        # 所有問題回答完成，生成推薦
        drink = user_data[user_id]["drink"]
        mood = user_data[user_id]["mood"]
        taste = user_data[user_id]["taste"]
        occasion = user_data[user_id]["occasion"]
        weather = user_data[user_id]["weather"]
        
        recommendation = GPT_recommendation(drink, mood, taste, occasion, weather)
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(recommendation))

        # 清空使用者資料
        user_data[user_id] = {"drink": None, "mood": None, "taste": None, "occasion": None, "weather": None}
