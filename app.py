from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    MessageAction,
    LocationMessage,
    TemplateMessage,
    LocationAction,
    ButtonsTemplate,
    QuickReply,
    QuickReplyItem,
    FlexMessage,
    FlexContainer,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    LocationMessageContent
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3 import (
    WebhookHandler
)

from flask import Flask, request, abort
from argparse import ArgumentParser
import sys
import os
from dotenv import load_dotenv
import json
import pandas as pd

from database import Database, CSVData

load_dotenv()

app = Flask(__name__)

# Database
db = Database('test.db')
if not db.table_exists('my_table'):
    db.create_table('my_table', ['id TEXT PRIMARY KEY', 'status TEXT', 'lat TEXT', 'lng TEXT'])
    print('Table created.')
quick_options = [
    QuickReplyItem(
        action=MessageAction(label="便當", text="便當")
    ),
    QuickReplyItem(
        action=MessageAction(label="小吃店", text="小吃店")
    ),
    QuickReplyItem(
        action=MessageAction(label="滷味", text="滷味")
    ),
    QuickReplyItem(
        action=MessageAction(label="炸物", text="炸物")
    ),
    QuickReplyItem(
        action=MessageAction(label="早餐", text="早餐")
    ),
    QuickReplyItem(
        action=MessageAction(label="宵夜", text="宵夜")
    ),
]


def cal_distance(lat1, lon1, lat2, lon2):
    from math import sin, cos, sqrt, atan2, radians
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return '{:.2f} KM'.format(distance)

def get_flex_message(name, star, review, typ, distance, pros, cons, url, img):
    flex_message = '''
{
  "type": "bubble",
  "hero": {
    "type": "image",
    "url": "https://developers-resource.landpress.line.me/fx/img/01_1_cafe.png",
    "size": "full",
    "aspectRatio": "20:13",
    "aspectMode": "cover"
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "Brown Cafe",
        "weight": "bold",
        "size": "xl"
      },
      {
        "type": "box",
        "layout": "baseline",
        "margin": "md",
        "contents": [
          {
            "type": "icon",
            "size": "sm",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
          },
          {
            "type": "icon",
            "size": "sm",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
          },
          {
            "type": "icon",
            "size": "sm",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
          },
          {
            "type": "icon",
            "size": "sm",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
          },
          {
            "type": "icon",
            "size": "sm",
            "url": "https://developers-resource.landpress.line.me/fx/img/review_gray_star_28.png"
          },
          {
            "type": "text",
            "text": "4.0",
            "size": "sm",
            "color": "#999999",
            "margin": "md",
            "flex": 0
          },
          {
            "type": "text",
            "text": "(123)",
            "size": "sm",
            "color": "#999999",
            "margin": "md",
            "flex": 0
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "margin": "lg",
        "spacing": "sm",
        "contents": [
          {
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [
              {
                "type": "text",
                "text": "類型",
                "color": "#aaaaaa",
                "size": "sm",
                "flex": 1
              },
              {
                "type": "text",
                "text": "Flex Tower, 7-7-4 Midori-ku, Tokyo",
                "wrap": true,
                "color": "#666666",
                "size": "sm",
                "flex": 5
              }
            ]
          },
          {
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [
              {
                "type": "text",
                "text": "距離",
                "color": "#aaaaaa",
                "size": "sm",
                "flex": 1
              },
              {
                "type": "text",
                "text": "Flex Tower, 7-7-4 Midori-ku, Tokyo",
                "wrap": true,
                "color": "#666666",
                "size": "sm",
                "flex": 5
              }
            ]
          },
          {
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [
              {
                "type": "text",
                "text": "優點",
                "color": "#aaaaaa",
                "size": "sm",
                "flex": 1
              },
              {
                "type": "text",
                "text": "10:00 - 23:00",
                "wrap": true,
                "color": "#666666",
                "size": "sm",
                "flex": 5
              }
            ]
          },
          {
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [
              {
                "type": "text",
                "text": "缺點",
                "color": "#aaaaaa",
                "size": "sm",
                "flex": 1
              },
              {
                "type": "text",
                "text": "10:00 - 23:00",
                "wrap": true,
                "color": "#666666",
                "size": "sm",
                "flex": 5
              }
            ]
          }
        ]
      }
    ]
  },
  "footer": {
    "type": "box",
    "layout": "vertical",
    "spacing": "sm",
    "contents": [
      {
        "type": "button",
        "style": "link",
        "height": "sm",
        "action": {
          "type": "uri",
          "label": "開啟 Google Map 導航",
          "uri": "https://line.me/"
        }
      }
    ],
    "flex": 0
  }
}
'''
    gold_star = "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
    gray_star = "https://developers-resource.landpress.line.me/fx/img/review_gray_star_28.png"
    json_data = json.loads(flex_message)
    json_data['body']['contents'][0]['text'] = name
    for i in range(5):
        if i < int(star):
            json_data['body']['contents'][1]['contents'][i]['url'] = gold_star
        else:
            json_data['body']['contents'][1]['contents'][i]['url'] = gray_star
    json_data['body']['contents'][1]['contents'][5]['text'] = str(star)
    json_data['body']['contents'][1]['contents'][6]['text'] = f'({review})'
    
    json_data['body']['contents'][2]['contents'][0]['contents'][1]['text'] = typ
    json_data['body']['contents'][2]['contents'][1]['contents'][1]['text'] = distance
    json_data['body']['contents'][2]['contents'][2]['contents'][1]['text'] = pros
    json_data['body']['contents'][2]['contents'][3]['contents'][1]['text'] = cons
    json_data['footer']['contents'][0]['action']['uri'] = url
    json_data['hero']['url'] = img
    return json_data

def get_carousel_message(flex_message_list):
    flex_message = '{"type": "carousel","contents": ['
    flex_message = {
        "type": "carousel",
        "contents": flex_message_list
    }
    return json.dumps(flex_message, ensure_ascii=False)

# init shop data
csv_data = CSVData('result.csv')
shop_data = csv_data.get_data()

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # 檢查是否已經存在該記錄
        user_id = event.source.user_id
        # print(user_id)
        db_data = db.read_data('my_table')
        if db_data != []:
            result = [data for data in db_data if data[0] == user_id]
            if result == []:
              user_data = db.insert_data('my_table', (user_id, '0', '', ''))
            else:
              user_data = result[0]
        else:
            user_data = db.insert_data('my_table', (user_id, '0', '', ''))

        # print(user_data)
        msg = [] # 回覆訊息

        if user_data[1] == '2': # 2: 重置
            print('reset user data')
            user_data = db.insert_data('my_table', (user_id, '0', '', ''))
        print(user_data)
        if user_data[1] == '0': # 0: 未選擇位置
            print('user not select location')
            buttons_template = ButtonsTemplate(
            text='請在地圖上選擇所在位置',
            actions=[
                    LocationAction(
                        label='傳送位置',
                    )
                ]
            )
            msg.append(TextMessage(text='你還沒告訴我你的位置呦！'))
            msg.append(TemplateMessage(alt_text='請在地圖上選擇所在位置',
                    template=buttons_template)),
        elif user_data[1] == '1': # 1: 未選擇類型
            print('user not select type')
            if event.message.text in ['便當', '小吃店', '滷味', '炸物', '早餐', '宵夜']:
                db.insert_data('my_table', (user_id, '2', user_data[2], user_data[3]))
                shops = [data for data in shop_data if event.message.text == csv_data.get_cell_by_key(data, 'typ')]
                a = json.loads(shops[0][11])['pros']
                # print('、'.join(a))
                shops.sort(key=lambda x: cal_distance(float(user_data[2]), float(user_data[3]), float(csv_data.get_cell_by_key(x, 'location').split(', ')[0]), float(csv_data.get_cell_by_key(x, 'location').split(', ')[1])))
                flex_message_list = [
                        get_flex_message(
                        name=csv_data.get_cell_by_key(shop, 'name'),
                        star=csv_data.get_cell_by_key(shop, 'star'),
                        review=csv_data.get_cell_by_key(shop, 'review'),
                        typ=csv_data.get_cell_by_key(shop, 'typ'),
                        distance=str(cal_distance(float(user_data[2]), float(user_data[3]), float(csv_data.get_cell_by_key(shop, 'location').split(', ')[0]), float(csv_data.get_cell_by_key(shop, 'location').split(', ')[1]))),
                        pros='\n'.join(json.loads(csv_data.get_cell_by_key(shop, 'keyword'))['pros']),
                        cons='\n'.join(json.loads(csv_data.get_cell_by_key(shop, 'keyword'))['cons']),
                        url=csv_data.get_cell_by_key(shop, 'url'),
                        img=csv_data.get_cell_by_key(shop, 'img')
                      ) for shop in shops
                    ]
                
                flex_message = get_carousel_message(flex_message_list)
                # print(flex_message)
                msg.append(TextMessage(text='好的！我們來幫你找吃的！'))
                msg.append(
                    FlexMessage(
                        alt_text='店家資訊',
                        contents=FlexContainer.from_json(flex_message)
                    )
                )
            else:
                quick_reply = QuickReply(
                    items=quick_options
                )
                msg.append(TextMessage(text='還沒告訴我你想吃哪種類型的呦！', quickReply=quick_reply))
        if msg != []:
            # 回覆訊息
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=msg
                )
            )


@handler.add(MessageEvent, message=LocationMessageContent)
def message_location(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        # print(event.message)

        user_id = event.source.user_id
        user_data = db.insert_data('my_table', (user_id, '1', event.message.latitude, event.message.longitude))

        # print(user_data)

        quick_reply = QuickReply(
            items=quick_options
        )
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text="請問你想吃哪種類型的呢？", quickReply=quick_reply)]
            )
        )


# init
if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
