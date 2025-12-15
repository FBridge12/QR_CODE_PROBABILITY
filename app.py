import os
import random
import redis
from flask import Flask, make_response, request

app = Flask(__name__)


DEBUG_MODE = False
TOTAL_SCANS = 52

redis_url = os.environ.get('REDIS_URL')
if redis_url:
    r = redis.from_url(redis_url)
else:
    print("Warning: No REDIS_URL found.")
    r = None

def get_winner_html(is_replay=False):
    extra_text = "<p style='color:#e67e22; font-size:0.9em'>(KẾT QUẢ ĐÃ LƯU)</p>" if is_replay else ""
    return f"""
        <h1>🎉 CHÚC MỪNG! 🎉</h1>
        <h2>BẠN ĐÃ TRÚNG THƯỞNG RÙIII!</h2>
        <p>Cho mình xem để nhận quà nhaaa.</p>
        {extra_text}
    """


def get_loser_html(is_replay=False):
    extra_text = "<p style='color:#e67e22; font-size:0.9em'>(KẾT QUẢ ĐÃ LƯU)</p>" if is_replay else ""
    return f"""
        <h1>Tiếc quá... 😢</h1>
        <p>Bạn không trúng thưởng rùi...</p>
        <p>Chúc bạn may mắn lần sau nhaa!</p>
        {extra_text}
    """


def create_html(content, color="#333"):
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kết quả quay thưởng</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                text-align: center; padding: 40px 20px; background-color: #f9f9f9;
            }}
            .container {{
                background: white; padding: 30px; border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto;
            }}
            h1 {{ color: {color}; margin-bottom: 10px; }}
            p {{ color: #555; font-size: 1.1em; line-height: 1.6; }}
            .debug {{ color: red; font-size: 0.8em; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">{content}</div>
    </body>
    </html>
    """


def init_game():
    if r and not r.exists("winning_number"):
        winning_num = random.randint(1, TOTAL_SCANS)
        r.set("winning_number", winning_num)
        r.set("scan_count", 0)
        r.set("prize_claimed", "false")


@app.route('/')
def scan_qr():
    init_game()

    existing_result = request.cookies.get('raffle_result')

    if not DEBUG_MODE and existing_result:
        if existing_result == 'win':
            return create_html(get_winner_html(is_replay=True), color="#27ae60")
        elif existing_result == 'lose':
            return create_html(get_loser_html(is_replay=True), color="#c0392b")

    if r.get("prize_claimed").decode('utf-8') == "true":
        msg = "<h1>😔 Rất tiếc!</h1><p>Phần thưởng đã có người may mắn trúng trước đó.</p>"
        resp = make_response(create_html(msg, color="#7f8c8d"))
        resp.set_cookie('raffle_result', 'lose', max_age=86400)
        return resp

    current_count = r.incr("scan_count")
    winning_number = int(r.get("winning_number"))

    if current_count == winning_number:
        r.set("prize_claimed", "true")
        result_type = 'win'
        html_msg = get_winner_html()
        theme_color = "#27ae60"
    else:
        result_type = 'lose'
        html_msg = get_loser_html()
        theme_color = "#c0392b"

    if DEBUG_MODE:
        html_msg += f"""<div class="debug">DEBUG: Scan #{current_count} (Winner is #{winning_number})<br><a href="/reset">Reset</a></div>"""

    resp = make_response(create_html(html_msg, color=theme_color))

    resp.set_cookie('raffle_result', result_type, max_age=86400)

    return resp


@app.route('/reset')
def reset_game():
    if r:
        r.delete("winning_number")
        r.delete("scan_count")
        r.delete("prize_claimed")
        return create_html("<h1>Game Reset!</h1><p><a href='/'>Back</a></p>", color="blue")
    return "Redis not connected"


if __name__ == '__main__':

    app.run()

