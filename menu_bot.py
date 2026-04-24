import requests
from bs4 import BeautifulSoup
import os
import subprocess
import base64
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

URL = "http://pvv.co.kr/bbs/index.php?code=bbs_menu01"
WEBHOOK_URL = os.environ["TEAMS_WEBHOOK"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = "nayoung240/cafeteria-menu-bot"

def fetch_latest_post():
    res = requests.get(URL, timeout=10)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")

    link = soup.select_one("td.bbs_blue_gray a")
    if not link:
        return None, None

    title = link.get_text(strip=True)
    post_url = "http://pvv.co.kr/bbs/" + link["href"]
    return title, post_url

def download_pdf(post_url):
    pdf_path = "/tmp/menu.pdf"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(post_url, wait_until="networkidle")

        with page.expect_download() as download_info:
            page.click("a[href*='fileDown']")

        download = download_info.value
        download.save_as(pdf_path)
        browser.close()

    return pdf_path

def pdf_to_image(pdf_path):
    img_prefix = "/tmp/menu"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "300", "-f", "1", "-l", "1", pdf_path, img_prefix],
        check=True
    )
    with open("/tmp/menu-1.png", "rb") as f:
        return f.read()

def upload_image(img_data):
    """GitHub repo에 이미지를 커밋하고 raw URL을 반환"""
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    file_path = f"images/menu_{now.strftime('%Y%m%d')}.png"

    encoded = base64.b64encode(img_data).decode()

    # 기존 파일이 있으면 sha 가져오기 (덮어쓰기용)
    sha = None
    check = requests.get(
        f"https://api.github.com/repos/{REPO}/contents/{file_path}",
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        timeout=15
    )
    if check.status_code == 200:
        sha = check.json().get("sha")

    payload = {
        "message": f"menu: {now.strftime('%Y-%m-%d')} 식단 이미지",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha

    res = requests.put(
        f"https://api.github.com/repos/{REPO}/contents/{file_path}",
        json=payload,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        timeout=30
    )
    res.raise_for_status()

    raw_url = f"https://raw.githubusercontent.com/{REPO}/main/{file_path}"
    print(f"이미지 업로드 완료: {raw_url}")
    return raw_url

def post_to_teams(title, image_url):
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"🍱 {title}",
                            "weight": "Bolder",
                            "size": "Medium",
                            "wrap": True
                        },
                        {
                            "type": "Image",
                            "url": image_url,
                            "size": "Stretch",
                            "msTeams": {"allowExpand": True}
                        }
                    ]
                }
            }
        ]
    }
    res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    print(f"Teams 응답: {res.status_code} / {res.text}")
    res.raise_for_status()

if __name__ == "__main__":
    title, post_url = fetch_latest_post()
    if not title:
        print("게시글을 찾지 못했습니다")
        raise SystemExit(1)

    pdf_path = download_pdf(post_url)
    img_data = pdf_to_image(pdf_path)
    image_url = upload_image(img_data)
    post_to_teams(title, image_url)
    print(f"Teams에 메뉴 전송 완료: {image_url}")
