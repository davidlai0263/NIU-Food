from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    LocationMessage,
    TemplateMessage,
    LocationAction,
    ButtonsTemplate,
    QuickReply,
    QuickReplyItem
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

load_dotenv()

app = Flask(__name__)

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
        buttons_template = ButtonsTemplate(
            text='請在地圖上選擇所在位置',
            actions=[
                LocationAction(
                    label='傳送位置',
                )
            ]
        )

        # 回覆訊息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TemplateMessage(
                    alt_text='請在地圖上選擇所在位置',
                    template=buttons_template),
                ]
            )
        )


@handler.add(MessageEvent, message=LocationMessageContent)
def message_location(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        print(event.message)
        quick_reply = QuickReply(
            items=[
                QuickReplyItem(
                    action=LocationAction(label="傳送位置")
                )
            ]
        )
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text="請問您還需要什麼服務嗎？", quickReply=quick_reply)]
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
