import requests
from bs4 import BeautifulSoup
import os

URL = "http://pvv.co.kr/bbs/index.php?code=bbs_menu01"
WEBHOOK_URL = os.environ["TEAMS_WEBHOOK"]

def fetch_menu():
    res = requests.get(URL, timeout=10)
    res.encoding = "euc-kr"  # 한국 사이트 인코딩
    soup = BeautifulSoup(res.text, "html.parser")

    # 최신 게시글 링크 추출 (실제 HTML 구조 확인 후 셀렉터 조정 필요)
    first_post = soup.select_one("table.bbs_list tbody tr td.subject a")
    if not first_post:
        return None, None

    post_url = "http://pvv.co.kr/bbs/" + first_post["href"]
    title = first_post.get_text(strip=True)

    # 게시글 본문 크롤링
    post_res = requests.get(post_url, timeout=10)
    post_res.encoding = "euc-kr"
    post_soup = BeautifulSoup(post_res.text, "html.parser")

    content = post_soup.select_one("div.bbs_content, td.content")
    menu_text = content.get_text(separator="\n", strip=True) if content else ""

    return title, menu_text

def post_to_teams(title, menu_text):
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "0078D4",
        "title": f"🍱 {title}",
        "text": menu_text.replace("\n", "<br>")
    }
    requests.post(WEBHOOK_URL, json=payload, timeout=10)

if __name__ == "__main__":
    title, menu = fetch_menu()
    if title and menu:
        post_to_teams(title, menu)
        print("Teams에 메뉴 전송 완료")
    else:
        print("메뉴를 가져오지 못했습니다")
