import requests
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

USER_ID = "486906719"
BASE_URL = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={USER_ID}"
RSS_FILE = "bilibili_dynamic.rss"
LAST_ID_FILE = "last_dynamic_id.txt"

def get_dynamics():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://space.bilibili.com/{USER_ID}/dynamic"
    }
    
    try:
        response = requests.get(BASE_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def parse_dynamics(data):
    if not data or data["code"] != 0:
        return []
    
    items = []
    for item in data["data"]["items"]:
        # 只处理视频动态（类型 8）
        if item["type"] == 8:
            dynamic_id = item["id_str"]
            pub_date = datetime.fromtimestamp(item["modules"]["module_author"]["pub_ts"])
            
            # 提取视频信息
            video_info = item["modules"]["module_dynamic"]["major"]["archive"]
            video_url = f"https://www.bilibili.com/video/{video_info['aid']}"
            title = video_info["title"]
            desc = item["modules"]["module_dynamic"]["desc"]["text"]
            
            items.append({
                "id": dynamic_id,
                "title": title,
                "link": video_url,
                "description": desc,
                "pubDate": pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
            })
    
    return items

def update_rss(new_items):
    # 创建或更新 RSS 文件
    if not os.path.exists(RSS_FILE):
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "B站用户动态更新"
        ET.SubElement(channel, "link").text = f"https://space.bilibili.com/{USER_ID}/dynamic"
        ET.SubElement(channel, "description").text = "B站用户动态更新监控"
    else:
        tree = ET.parse(RSS_FILE)
        rss = tree.getroot()
        channel = rss.find("channel")

    # 添加新项目
    for item in reversed(new_items):  # 保持时间顺序
        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = item["title"]
        ET.SubElement(entry, "link").text = item["link"]
        ET.SubElement(entry, "description").text = item["description"]
        ET.SubElement(entry, "pubDate").text = item["pubDate"]
        ET.SubElement(entry, "guid").text = item["id"]

    # 美化 XML 输出
    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
    with open(RSS_FILE, "w", encoding="utf-8") as f:
        f.write(xml_str)

def check_update():
    # 读取上次检查的最后一个动态ID
    last_id = ""
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f:
            last_id = f.read().strip()

    data = get_dynamics()
    if not data:
        return

    new_items = []
    current_max_id = ""
    for item in parse_dynamics(data):
        current_max_id = item["id"]  # API 返回按时间倒序排列
        if item["id"] == last_id:
            break
        new_items.append(item)

    # 更新记录
    if current_max_id and current_max_id != last_id:
        with open(LAST_ID_FILE, "w") as f:
            f.write(current_max_id)

    # 如果有新内容则更新 RSS
    if new_items:
        update_rss(new_items)
        print(f"发现 {len(new_items)} 条新动态")
    else:
        print("没有发现新动态")

if __name__ == "__main__":
    check_update()
