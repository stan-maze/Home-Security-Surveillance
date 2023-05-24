import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

CURRENT_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(os.path.dirname(CURRENT_PATH))
config_PATH = os.path.join(DIR_PATH, 'utils', 'em_config.json')
with open(config_PATH) as f:
    config = json.load(f)
    
def send_email(recipient_email, subject, body):
    # 读取配置文件

    # 从配置文件中获取参数
    smtp_server = config['smtp_server']
    smtp_port = config['smtp_port']
    sender_email = config['sender_email']
    password = config['password']

    # 创建包含邮件内容的MIMEMultipart对象
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    # 邮件正文
    message.attach(MIMEText(body, 'plain'))

    # 连接到SMTP服务器
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        # 登录到SMTP服务器
        server.login(sender_email, password)
        # 发送邮件
        result = server.send_message(message)

        # 检查邮件发送状态
        if not result:
            print('邮件发送成功')
            return True
        else:
            failed_recipients = result.keys()
            print(f'邮件发送失败，失败收件人：{failed_recipients}')
            return False

# 示例用法
# recipient_email = 'recipient@example.com'
# subject = '这是邮件的主题'
# body = '这是邮件的内容。'

# send_email(recipient_email, subject, body)
