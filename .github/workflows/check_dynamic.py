import requests
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

USER_ID = "486906719"
BASE_URL = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={USER_ID}"
RSS_FILE = "bilibili_dynamic.rss"
LAST_ID_FILE = "last_dynamic_id.txt"
cookie = "buvid3=32C7A099-802D-1D22-2916-55467146EED148177infoc; b_nut=1740473048; _uuid=9B75B198-4385-CBDF-54EC-10101B4D1A16BB49581infoc; buvid_fp=d8343e7c6587a5d571a7c669b4478c94; buvid4=6AD296B9-56B3-12A2-8162-3D27515A974749461-025022508-LqM5iGljEC8mrtSIprUkwg%3D%3D; DedeUserID=497740698; DedeUserID__ckMd5=c543ac17028c68af; header_theme_version=CLOSE; enable_web_push=DISABLE; home_feed_column=5; rpdid=|(u)l|~)|lR|0J'u~R|R~JkJ); hit-dyn-v2=1; enable_feed_channel=ENABLE; PVID=1; browser_resolution=2552-1322; opus-goback=1; LIVE_BUVID=AUTO3717429912684266; bp_t_offset_497740698=1051099018408493056; SESSDATA=09709422%2C1759130122%2C3dbee%2A42CjC18wmXRJ-GW-U8buxUTAfOWsly0b0oOKRinaIWmFn0RXrphU6nv27rcy3Ylnur8R8SVm5iNlREME45RHJYV1ZQb2kzTTFuaWRxLWhVX2VCQ2JzeXBacS1Ua1RaS3RocW5LaWExREUzVlFfdTVRNElnZ2NMT1dCVzVCcVcyUFhJdThIX2Nodl9RIIEC; bili_jct=74ca65df79a09cdfac48c8428df33c58; CURRENT_FNVAL=2000"

def get_dynamics():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://space.bilibili.com/{USER_ID}/dynamic",
        "Cookie": "buvid3=32C7A099-802D-1D22-2916-55467146EED148177infoc; b_nut=1740473048; _uuid=9B75B198-4385-CBDF-54EC-10101B4D1A16BB49581infoc; buvid_fp=d8343e7c6587a5d571a7c669b4478c94; buvid4=6AD296B9-56B3-12A2-8162-3D27515A974749461-025022508-LqM5iGljEC8mrtSIprUkwg%3D%3D; DedeUserID=497740698; DedeUserID__ckMd5=c543ac17028c68af; header_theme_version=CLOSE; enable_web_push=DISABLE; home_feed_column=5; rpdid=|(u)l|~)|lR|0J'u~R|R~JkJ); hit-dyn-v2=1; enable_feed_channel=ENABLE; PVID=1; browser_resolution=2552-1322; opus-goback=1; LIVE_BUVID=AUTO3717429912684266; bp_t_offset_497740698=1051099018408493056; SESSDATA=09709422%2C1759130122%2C3dbee%2A42CjC18wmXRJ-GW-U8buxUTAfOWsly0b0oOKRinaIWmFn0RXrphU6nv27rcy3Ylnur8R8SVm5iNlREME45RHJYV1ZQb2kzTTFuaWRxLWhVX2VCQ2JzeXBacS1Ua1RaS3RocW5LaWExREUzVlFfdTVRNElnZ2NMT1dCVzVCcVcyUFhJdThIX2Nodl9RIIEC; bili_jct=74ca65df79a09cdfac48c8428df33c58; CURRENT_FNVAL=2000"
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
        if item["type"] == 'DYNAMIC_TYPE_AV':
            dynamic_id = item["id_str"]
            pub_date = datetime.fromtimestamp(item["modules"]["module_author"]["pub_ts"])
            
            # 提取视频信息
            video_info = item["modules"]["module_dynamic"]["major"]["archive"]
            video_url = f"https://www.bilibili.com/video/{video_info['bvid']}"
            title = video_info["title"]
            #desc = item["modules"]["module_dynamic"]["major"]["archive"]["desc"]
            
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