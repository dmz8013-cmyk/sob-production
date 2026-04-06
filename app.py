import os
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='.', static_folder='static')

KST = timezone(timedelta(hours=9))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        company = data.get('company', '').strip()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        inquiry_type = data.get('inquiry_type', '').strip()
        content = data.get('content', '').strip()

        if not all([company, name, phone, email, inquiry_type, content]):
            return jsonify({'success': False, 'message': '모든 필수 항목을 입력해주세요.'}), 400

        now_kst = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')

        send_telegram_notification(company, name, phone, email, inquiry_type, content, now_kst)

        return jsonify({'success': True, 'message': '상담 신청이 완료되었습니다. 24시간 내 연락드리겠습니다.'})

    except Exception as e:
        app.logger.error(f'폼 제출 처리 실패: {e}')
        return jsonify({'success': False, 'message': '일시적 오류가 발생했습니다. dmz8013@gmail.com으로 직접 문의해주세요.'}), 500


def send_telegram_notification(company, name, phone, email, inquiry_type, content, timestamp):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print('[TELEGRAM] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 미설정 — 알림 스킵')
        return

    text = (
        f"🔔 <b>[SOB 상담신청]</b>\n"
        f"\n"
        f"회사명: {company}\n"
        f"담당자: {name}\n"
        f"연락처: {phone}\n"
        f"이메일: {email}\n"
        f"문의유형: {inquiry_type}\n"
        f"문의내용: {content}\n"
        f"\n"
        f"접수시각: {timestamp}"
    )

    try:
        resp = requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'},
            timeout=10
        )
        if resp.ok:
            print(f'[TELEGRAM] 알림 발송 완료: {name} ({company})')
        else:
            print(f'[TELEGRAM ERROR] API 응답: {resp.status_code} {resp.text}')
    except Exception as e:
        print(f'[TELEGRAM ERROR] 발송 실패: {e}')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
