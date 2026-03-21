import requests
from bs4 import BeautifulSoup
import os
import subprocess
import tempfile

URL = "http://pvv.co.kr/bbs/index.php?code=bbs_menu01"
WEBHOOK_URL = os.environ["TEAMS_WEBHOOK"]

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

def fetch_pdf_url(post_url):
    res = requests.get(post_url, timeout=10)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")

    pdf_link = soup.select_one("a[href*='fileDown']")
    if not pdf_link:
        return None

    return "http://pvv.co.kr/bbs/" + pdf_link["href"]

def pdf_to_image(pdf_url):
    headers = {
        "Referer": "http://pvv.co.kr/bbs/index.php?code=bbs_menu01",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    }
    pdf_data = requests.get(pdf_url, headers=headers, timeout=30).content

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "menu.pdf")
        img_prefix = os.path.join(tmpdir, "menu")

        with open(pdf_path, "wb") as f:
            f.write(pdf_data)

        # PDF 첫 페이지를 PNG로 변환 (poppler-utils 필요)
        subprocess.run(
            ["pdftoppm", "-png", "-r", "150", "-f", "1", "-l", "1", pdf_path, img_prefix],
            check=True
        )

        img_path = os.path.join(tmpdir, "menu-1.png")
        with open(img_path, "rb") as f:
            img_data = f.read()

    return img_data

def upload_image(img_data):
    # catbox.moe 무료 이미지 호스팅 (API 키 불필요)
    res = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": ("menu.png", img_data, "image/png")},
        timeout=30
    )
    return res.text.strip()  # 업로드된 이미지 URL 반환

def post_to_teams(title, image_url):
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "0078D4",
        "title": f"🍱 {title}",
        "sections": [
            {
                "images": [{"image": image_url}]
            }
        ]
    }
    requests.post(WEBHOOK_URL, json=payload, timeout=10)

if __name__ == "__main__":
    title, post_url = fetch_latest_post()
    if not title:
        print("게시글을 찾지 못했습니다")
        raise SystemExit(1)

    pdf_url = fetch_pdf_url(post_url)
    if not pdf_url:
        print("PDF를 찾지 못했습니다")
        raise SystemExit(1)

    img_data = pdf_to_image(pdf_url)
    image_url = upload_image(img_data)
    post_to_teams(title, image_url)
    print(f"Teams에 메뉴 전송 완료: {image_url}")
