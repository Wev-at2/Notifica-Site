from flask import Flask
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, time
import os
from flask_cors import CORS
import threading
import time as time_module
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Carrega variáveis de ambiente
load_dotenv()
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

# Variáveis globais
access_count = 0
visit_log = defaultdict(int)  # Ex: {'17:00': 3}
lock = threading.Lock()

def send_daily_email(count, log):
    try:
        now = datetime.now()

        if log:
            time_list_html = "<ul>" + "".join(
                f"<li>{hour} → {visits} visita(s)</li>" for hour, visits in sorted(log.items())
            ) + "</ul>"
        else:
            time_list_html = "<p>Nenhuma visita registrada hoje.</p>"

        html_content = f"""
        <html>
        <body>
        <p>Hoje seu portfólio recebeu <strong>{count}</strong> visita(s)! 🤩🙏</p>
        <p>Relatório diário de acessos - {now.strftime('%d/%m/%Y')}</p>
        <p><strong>Horários das visitas:</strong></p>
        {time_list_html}
        <img src="GIF OU IMAGEM">
        </body>
        </html>
        """
        msg = MIMEText(html_content, 'html')
        msg['Subject'] = 'Relatório Diário de Visitas'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"[✔️] Relatório enviado com {count} acesso(s) em {now.strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"[❌] Erro ao enviar relatório: {e}")

def schedule_daily_report():
    while True:
        now = datetime.now()
        target = datetime.combine(now.date(), time(10, 30))

        if now > target:
            target = target.replace(day=now.day + 1)

        wait_seconds = (target - now).total_seconds()
        print(f"Próximo envio programado para às 18h. Aguardando {wait_seconds:.0f} segundos...")
        time_module.sleep(wait_seconds)

        with lock:
            global access_count, visit_log
            send_daily_email(access_count, visit_log)
            access_count = 0
            visit_log = defaultdict(int)

# Inicia a thread de agendamento
report_thread = threading.Thread(target=schedule_daily_report, daemon=True)
report_thread.start()

@app.route('/')
def home():
    register_visit()
    return "Bem-vindo!"

@app.route('/track-visit')
def track_visit():
    register_visit()
    return '', 204

def register_visit():
    global access_count, visit_log
    with lock:
        access_count += 1
        hour_str = datetime.now().strftime('%H:%M')
        visit_log[hour_str] += 1
        print(f"Visita registrada às {hour_str} — Total: {access_count}")

if __name__ == '__main__':
    app.run(debug=True)
