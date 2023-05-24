import shutil
import datetime
import tarfile
import glob
import os

log_dir = 'log'  # 日志目录路径
archive_dir = 'log_archive'  # 归档目录路径
current_time = datetime.datetime.now()
if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

# 清理超过一个月的日志归档记录
one_month_ago = current_time - datetime.timedelta(seconds=30)
for archive_file in glob.glob(os.path.join(archive_dir, '*.tar.gz')):
    modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(archive_file))
    if modified_time < one_month_ago:
        os.remove(archive_file)
        print(f"Deleted archived log file: {archive_file}")

# 归档超过一周的日志目录并压缩
one_week_ago = current_time - datetime.timedelta(days=7)
for log_subdir in os.listdir(log_dir):
    log_subdir_path = os.path.join(log_dir, log_subdir)
    if not os.path.isdir(log_subdir_path):
        continue
    modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(log_subdir_path))
    if modified_time < one_week_ago:
        # 创建归档文件路径
        archive_file = os.path.join(archive_dir, f"{log_subdir}.tar.gz")

        # 压缩整个目录到归档文件
        with tarfile.open(archive_file, "w:gz") as tar:
            tar.add(log_subdir_path, arcname=log_subdir)

        # 删除原始日志目录
        shutil.rmtree(log_subdir_path)
        print(f"Archived and deleted log directory: {log_subdir_path} -> {archive_file}")
