import os
import sys
import django
dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(dir_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asparagus.settings")
django.setup()

from shutil import copy2
from datetime import datetime, timedelta
import pytz
from record.models import ImageList


# 指定开始和结束日期
total_start_date = datetime(2022, 3, 26, 0, 0, 0).astimezone(pytz.timezone('Asia/Taipei'))
total_end_date = datetime(2022, 9, 5, 0, 0, 0).astimezone(pytz.timezone('Asia/Taipei'))

# 指定目标文件夹的根路径
target_root_folder = '/ssd_sn570/asparagus_web/django_asparagus/img_select/'
os.makedirs(target_root_folder, exist_ok=True)

# 遍历日期范围
current_date = total_start_date
while current_date <= total_end_date:
    # 计算日期范围的起始和结束时间
    start_time = current_date.replace(hour=0, minute=0, second=0)
    end_time = current_date.replace(hour=23, minute=59, second=59)

    # 使用filter方法检索在指定日期范围内上传的照片
    filter_list = ImageList.objects.filter(date__range=[start_time, end_time])

    # 指定目标文件夹
    target_folder = os.path.join(target_root_folder, current_date.strftime("%Y%m%d"))

    # 确保目标文件夹存在，如果不存在，则创建
    if filter_list.exists():
        os.makedirs(target_folder, exist_ok=True)

    i = 0
    # 复制每张照片到目标文件夹中
    for photo in filter_list:
        source_path = str(photo.image.path)
        filename = os.path.basename(source_path)
        destination_path = os.path.join(target_folder, filename)

        # 检查目标文件夹是否已存在相同文件名的照片
        while os.path.exists(destination_path):
            base, ext = os.path.splitext(filename)
            filename = f"{base}_(2){ext}"
            destination_path = os.path.join(target_folder, filename)

        copy2(source_path, destination_path)
        print(f"    {filename = }")
        i += 1

    print(f"total {i} pics copied on {current_date.strftime('%Y-%m-%d')}")
    print()

    # 增加一天
    current_date += timedelta(days=1)
