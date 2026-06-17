import os
import csv
from datetime import datetime, timedelta
import config

def init_folders_and_logs():
    """初始化文件夹和 CSV 日志标题"""
    if not os.path.exists(config.RECORD_DIR):
        os.makedirs(config.RECORD_DIR)
    if not os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["触发时间", "检测身份", "最高置信度", "AI回应文本"])

def log_to_csv(identity, score, msg):
    """单次识别结果写入 CSV"""
    try:
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(config.LOG_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([now_str, identity, f"{score:.2f}", msg])
    except Exception as e:
        print(f"日志写入失败: {e}")

def get_today_visitors():
    """提取当日所有识别记录列表"""
    today_str = datetime.now().strftime('%Y-%m-%d')
    records = []
    if os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 4 and today_str in row[0]:
                    time_part = row[0].split()[1]
                    records.append({"name": row[1], "time": time_part})
    return records

def generate_weekly_report():
    """汇总生成近 7 天的本地文本安全周报"""
    one_week_ago = datetime.now() - timedelta(days=7)
    weekly_records = []

    if os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 4:
                    try:
                        row_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                        if row_time >= one_week_ago:
                            weekly_records.append(row)
                    except:
                        pass

    report_filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"============ 哨兵周报文件 ({datetime.now().strftime('%Y-%m-%d')}) ============\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"近一周安全事件总数: {len(weekly_records)} 次\n")
        f.write("----------------------------------------------------------------------\n")
        for r in weekly_records:
            f.write(f"时间: {r[0]} | 身份: {r[1]} | 置信度: {r[2]} | AI描述: {r[3]}\n")
    return report_filename, len(weekly_records)