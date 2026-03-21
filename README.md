# 구내식당 메뉴 Teams 자동화

매주 월요일 오전 8시(KST)에 구내식당 메뉴를 크롤링해서 Microsoft Teams로 자동 전송하는 봇입니다.

## 특징

- LLM 없이 순수 코드로 처리 (토큰 비용 0원)
- 별도 서버 불필요 (GitHub Actions 사용)
- 월 약 1분 Actions 사용 (무료 한도 내)

## 설정 방법

1. **리포지토리 Fork 또는 Clone**

2. **Teams Incoming Webhook 발급**
   - Teams 채널 우클릭 → 채널 편집
   - 커넥터 탭 → Incoming Webhook → 구성
   - 이름 입력 (예: `구내식당 메뉴`) → 만들기
   - 생성된 URL 복사

3. **GitHub Secret 등록**
   - 리포 → Settings → Secrets and variables → Actions
   - `TEAMS_WEBHOOK` 이름으로 Webhook URL 추가

4. **수동 테스트**
   - Actions 탭 → Weekly Cafeteria Menu → Run workflow

## 파일 구조

```
├── .github/
│   └── workflows/
│       └── menu.yml   # GitHub Actions 스케줄
└── menu_bot.py        # 크롤링 + Teams 전송 로직
```

## 참고

- 메뉴 출처: http://pvv.co.kr/bbs/index.php?code=bbs_menu01
- BeautifulSoup 셀렉터는 실제 페이지 HTML 구조에 따라 조정 필요
