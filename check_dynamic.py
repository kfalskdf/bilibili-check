from dotenv import load_dotenv
import requests
from datetime import datetime
from feedgen.feed import FeedGenerator
import os
import pytz

USER_ID = "486906719"
BASE_URL = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={USER_ID}"
RSS_FILE = "bilibili_dynamic.xml"
LAST_ID_FILE = "last_dynamic_id.txt"
load_dotenv()  # 在文件开头添加

def get_dynamics():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://space.bilibili.com/{USER_ID}/dynamic",
        "Cookie": os.getenv("BILI_COOKIE", "")  # 建议通过环境变量传入
    }
    
    try:
        response = requests.get(BASE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 请求失败: {str(e)}")
        return None

def parse_dynamics(data):
    if not data or data.get("code") != 0:
        print(f"[WARNING] 无效的API响应: {data.get('message', '未知错误')}")
        return []
    
    items = []
    for item in data["data"]["items"]:
        try:
            if item["type"] == 'DYNAMIC_TYPE_AV':
                dynamic_id = item["id_str"]
                pub_date = datetime.fromtimestamp(
                    item["modules"]["module_author"]["pub_ts"],
                    tz=pytz.timezone('Asia/Shanghai')
                )
                
                video_info = item["modules"]["module_dynamic"]["major"]["archive"]
                items.append({
                    "id": dynamic_id,
                    "title": video_info["title"],
                    "link": f"https://www.bilibili.com/video/{video_info['bvid']}",
                    # "description": video_info["desc"],
                    "description": f"<img src='{video_info['cover']}'/><p>介绍：{video_info["desc"]}</p><p>地址：https://www.bilibili.com/video/{video_info['bvid']}</p>",
                    "pub_date": pub_date,
                    "author": item["modules"]["module_author"]["name"]
                })
        except KeyError as e:
            print(f"[WARNING] 解析动态时缺少关键字段: {str(e)}")
            continue
    
    return items

def update_rss(new_items):
    fg = FeedGenerator()
    fg.id(f"https://space.bilibili.com/{USER_ID}")
    fg.title(f"B站 {USER_ID} 动态更新")
    fg.link(href=f"https://space.bilibili.com/{USER_ID}/dynamic", rel="alternate")
    fg.description("自动生成的B站用户动态订阅")
    fg.language('zh-CN')
    
    # 合并历史记录和新条目
    if os.path.exists(RSS_FILE):
        try:
            old_feed = FeedGenerator()
            old_feed.parse(RSS_FILE)
            for entry in old_feed.entry():
                if any(e.id() == entry.id() for e in fg.entry()):
                    continue
                fe = fg.add_entry()
                fe.id(entry.id())
                fe.title(entry.title())
                fe.link(href=entry.link())
                fe.description(entry.description())
                fe.published(entry.published())
        except Exception as e:
            print(f"[WARNING] 读取历史RSS失败: {str(e)}")
    
    # 添加新条目（按发布时间排序）
    for item in sorted(new_items, key=lambda x: x["pub_date"]):
        fe = fg.add_entry()
        fe.id(item["id"])
        fe.title(item["title"])
        fe.link(href=item["link"])
        fe.description(item["description"])
        fe.published(item["pub_date"].astimezone(pytz.utc))
        fe.author(name=item["author"])
    
    # 生成符合标准的RSS
    fg.rss_file(RSS_FILE, pretty=True)

def check_update():
    last_id = ""
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f:
            last_id = f.read().strip()
    
    data = get_dynamics()
    if not data:
        return
    
    new_items = []
    current_max_id = last_id
    for item in parse_dynamics(data):
        if item["id"] == last_id:
            break
        if not current_max_id or item["id"] > current_max_id:
            current_max_id = item["id"]
        new_items.append(item)
    
    if new_items:
        update_rss(new_items)
        print(f"发现 {len(new_items)} 条新动态")
        with open(LAST_ID_FILE, "w") as f:
            f.write(current_max_id)
    else:
        print("没有新动态")

if __name__ == "__main__":
    check_update()