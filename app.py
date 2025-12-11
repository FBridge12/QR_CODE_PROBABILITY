import os
import random
import redis
from flask import Flask, make_response, request

app = Flask(__name__)

TOTAL_SCANS = 60
redis_url = os.environ.get('REDIS_URL')
r = redis.from_url(redis_url)

if not r.exists("winning_number"):
    winning_num = random.randint(1, TOTAL_SCANS)
    r.set("winning_number", winning_num)
    r.set("scan_count", 0)
    r.set("prize_claimed", "false")

def create_html(content, color="#333"):
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kết quả quay thưởng</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; padding: 50px 20px; }}
            h1 {{ color: {color}; }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """

@app.route('/')
def scan_qr():
    if request.cookies.get('has_played'):
        msg = "<h1>⚠️ Bạn đã quét mã này rồi!</h1><p>Bạn ơi, quét 1 lần thui...</p>"
        return create_html(msg, color="#e67e22")

    if r.get("prize_claimed").decode('utf-8') == "true":
        msg = "<h1>😔 HUHU </h1><p>Có bạn lấy phần thưởng mất rùiiii :<<.</p>"
        resp = make_response(create_html(msg, color="#7f8c8d"))
        resp.set_cookie('has_played', 'true')
        return resp

    current_count = r.incr("scan_count")
    winning_number = int(r.get("winning_number"))

    if current_count == winning_number:
        r.set("prize_claimed", "true")
        msg = """
        <h1>🎉 CHÚC MỪNG! 🎉</h1>
        <h2>Bạn quay trúng rùiiiii!</h2>
        <p>Đưa cho mình để nhận quà nha.</p>
        """
        html_content = create_html(msg, color="#27ae60")
    else:
        msg = """
        <h1>Tiếc quáaa</h1>
        <p>Chúc bạn may mắn lần sau nhaa!</p>
        """
        html_content = create_html(msg, color="#c0392b")

    resp = make_response(html_content)
    resp.set_cookie('has_played', 'true', max_age=86400)
    return resp

if __name__ == '__main__':
    app.run()