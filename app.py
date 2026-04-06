import os
import smtplib
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

        # 이메일 발송
        send_notification_email(
            company=company,
            name=name,
            phone=phone,
            email=email,
            inquiry_type=inquiry_type,
            content=content,
            timestamp=now_kst
        )

        return jsonify({'success': True, 'message': '상담 신청이 완료되었습니다. 24시간 내 연락드리겠습니다.'})

    except Exception as e:
        app.logger.error(f'폼 제출 처리 실패: {e}')
        return jsonify({'success': False, 'message': '일시적 오류가 발생했습니다. dmz8013@gmail.com으로 직접 문의해주세요.'}), 500


def send_notification_email(company, name, phone, email, inquiry_type, content, timestamp):
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    recipient = os.environ.get('MAIL_RECIPIENT', 'dmz8013@gmail.com')

    if not mail_username or not mail_password:
        app.logger.warning('MAIL_USERNAME 또는 MAIL_PASSWORD 환경변수 미설정 — 이메일 발송 스킵')
        return

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
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        app.logger.info(f'상담 알림 이메일 발송 완료: {name} ({company})')
    except Exception as e:
        app.logger.error(f'이메일 발송 실패: {e}')
        raise


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
