import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
        # 폼 데이터 또는 JSON
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

        # 디버그 로그
        _mu = os.environ.get('MAIL_USERNAME', '')
        _mp = os.environ.get('MAIL_PASSWORD', '')
        print(f'[DEBUG] MAIL_USERNAME: {_mu[:5]}***' if _mu else '[DEBUG] MAIL_USERNAME: (미설정)')
        print(f'[DEBUG] MAIL_PASSWORD length: {len(_mp)}' if _mp else '[DEBUG] MAIL_PASSWORD: (미설정)')

        # 이메일 비동기 발송
        print('[DEBUG] 이메일 백그라운드 발송 시작...')
        threading.Thread(
            target=send_notification_email,
            args=(company, name, phone, email, inquiry_type, content, now_kst)
        ).start()

        return jsonify({'success': True, 'message': '상담 신청이 완료되었습니다. 24시간 내 연락드리겠습니다.'})

    except Exception as e:
        app.logger.error(f'폼 제출 처리 실패: {e}')
        return jsonify({'success': False, 'message': '일시적 오류가 발생했습니다. dmz8013@gmail.com으로 직접 문의해주세요.'}), 500


def send_notification_email(company, name, phone, email, inquiry_type, content, timestamp):
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    recipient = os.environ.get('MAIL_RECIPIENT', 'dmz8013@gmail.com')

    if not mail_username or not mail_password:
        missing = []
        if not mail_username:
            missing.append('MAIL_USERNAME')
        if not mail_password:
            missing.append('MAIL_PASSWORD')
        raise RuntimeError(f'필수 환경변수 미설정: {", ".join(missing)}')

    subject = f'[SOB 상담신청] {inquiry_type} - {name}'

    body = f"""SOB Production 상담 신청이 접수되었습니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

회사명: {company}
담당자: {name}
연락처: {phone}
이메일: {email}
문의유형: {inquiry_type}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

문의내용:
{content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
접수시각: {timestamp}
"""

    msg = MIMEMultipart()
    msg['From'] = mail_username
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        print('[DEBUG] SMTP 연결 시도...')
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        print(f'[EMAIL] 발송 완료: {name} ({company})')
    except Exception as e:
        print(f'[EMAIL ERROR] 발송 실패: {e}')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
