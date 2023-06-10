import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import json
import os
from datetime import datetime, timedelta
import glob
import shutil
import logging
import tarfile

CURRENT_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(os.path.dirname(CURRENT_PATH))
config_PATH = os.path.join(DIR_PATH, 'utils', 'em_config.json')
log_dir = os.path.join(DIR_PATH, 'log')


with open(config_PATH) as f:
    config = json.load(f)
class alarm():
    def __init__(self) -> None:
        # 从配置文件中获取参数
        self.smtp_server = config['smtp_server']
        self.smtp_port = config['smtp_port']
        self.sender_email = config['sender_email']
        self.password = config['password']

    def setup(self, recipient_email):
        self.recipient_email = recipient_email
        print(self.recipient_email)
    
    def send_alert(self, subject, body, image_path):
        # 创建MIMEMultipart对象，并设置邮件头部信息
        print(self.recipient_email)
        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = self.recipient_email
        message['Subject'] = subject
        # 创建HTML格式的邮件正文
        html_body = f'''
        <html>
        <body>
            <p>{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}<p>
            <p>{body}</p>
            <img src="cid:image" alt="Image">
        </body>
        </html>
        '''
        # 将HTML正文转换为MIMEText对象，并添加到MIMEMultipart对象中
        message.attach(MIMEText(html_body, 'html'))

        # 读取图片文件，并创建图片附件
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image = MIMEImage(image_data)
        # 设置图片附件的Content-ID，供HTML中引用
        image.add_header('Content-ID', '<image>')
        message.attach(image)

        # 连接到SMTP服务器
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
            # 登录到SMTP服务器
            server.login(self.sender_email, self.password)
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
    

class logger():
    def __init__(self):
        pass
    
    def preprocess(self):
        # log_dir = 'log'  # 日志目录路径
        sub_log_dir = os.path.join(log_dir, 'log') # 日志目录路径
        archive_dir = os.path.join(log_dir, 'log_archive')  # 归档目录路径
        for required_dir in (log_dir, sub_log_dir, archive_dir):
            if not os.path.exists(required_dir):
                os.makedirs(required_dir)
        
        current_time = datetime.now()
        # 清理超过一个月的日志归档记录
        one_month_ago = current_time - timedelta(days=30)
        for archive_file in glob.glob(os.path.join(archive_dir, '*.tar.gz')):
            modified_time = datetime.fromtimestamp(os.path.getmtime(archive_file))
            if modified_time < one_month_ago:
                os.remove(archive_file)
                print(f"Deleted archived log file: {archive_file}")

        # 归档超过一周的日志目录并压缩
        one_week_ago = current_time - timedelta(days=7)
        for log_subdir in os.listdir(sub_log_dir):
            log_subdir_path = os.path.join(sub_log_dir, log_subdir)
            if not os.path.isdir(log_subdir_path):
                continue
            modified_time = datetime.fromtimestamp(os.path.getmtime(log_subdir_path))
            if modified_time < one_week_ago:
                # 创建归档文件路径
                archive_file = os.path.join(archive_dir, f"{log_subdir}.tar.gz")

                # 压缩整个目录到归档文件
                with tarfile.open(archive_file, "w:gz") as tar:
                    tar.add(log_subdir_path, arcname=log_subdir)

                # 删除原始日志目录
                shutil.rmtree(log_subdir_path)
                print(f"Archived and deleted log directory: {log_subdir_path} -> {archive_file}")

        self.sub_log_dir = sub_log_dir
        self.archive_dir = archive_dir
        
    def setup(self, maxMB, backupCount):
    # 创建按时间命名的目录
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        current_log_dir = os.path.join(self.sub_log_dir, current_time)
        os.makedirs(current_log_dir)

        # 更新日志文件路径
        log_file = os.path.join(current_log_dir, f'{current_time}.log')

        # 配置日志记录
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # 创建RotatingFileHandler对象，设置日志轮转条件
        log_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes= maxMB * 1024 * 1024,  # 每个日志文件的最大大小（字节）
            backupCount=backupCount,  # 保留的日志文件个数（包括当前文件）
        )
        log_handler.setLevel(logging.INFO)

        # 设置日志记录格式
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(log_formatter)

        # 添加日志处理器到logger
        logger.addHandler(log_handler)
        
        self.current_log_dir = current_log_dir
        self.logger = logger
        
    def log(self, information):
        self.logger.info(information)
        
        
    
    
def send_email(recipient_email, subject, body, image_path):
    # 读取配置文件

    # 从配置文件中获取参数
    smtp_server = config['smtp_server']
    smtp_port = config['smtp_port']
    sender_email = config['sender_email']
    password = config['password']

# 创建MIMEMultipart对象，并设置邮件头部信息
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    # 创建HTML格式的邮件正文
    html_body = f'''
    <html>
    <body>
        <p>{body}</p>
        <img src="cid:image" alt="Image">
    </body>
    </html>
    '''
    # 将HTML正文转换为MIMEText对象，并添加到MIMEMultipart对象中
    message.attach(MIMEText(html_body, 'html'))

    # 读取图片文件，并创建图片附件
    with open(image_path, 'rb') as f:
        image_data = f.read()
    image = MIMEImage(image_data)
    # 设置图片附件的Content-ID，供HTML中引用
    image.add_header('Content-ID', '<image>')
    message.attach(image)

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
# recipient_email = '2311306511@qq.com'
# subject = '这是邮件的主题'
# body = '这是邮件的内容。'

# send_email(recipient_email, subject, body, 'obama1.jpg')
