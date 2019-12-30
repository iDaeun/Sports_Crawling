from urllib.request import urlopen
from urllib.error import HTTPError
import json
import logging
from config import TargetConfig
import ssl
from datetime import datetime, time, timedelta
from time import sleep
import pymysql
import argparse
from bs4 import BeautifulSoup
import html5lib

# 경기결과
# - 1일전~오늘 경기 결과 API 정보 불러와 노출
# - 수집 사이트 : 네이버 스포츠 오늘의 경기 https://sports.news.naver.com/scoreboard/index.nhn?date=20191125
# - 수집 정보  : 날짜(월.일), 대회, 경기일정 및 결과 (종료된 경기에 한함)
# - 경기결과 15개 노출  
# : 노출 순서는 최근 시작한 경기부터 오래전에 시작한 경기 순으로 노출함.
# : 15개 경기 선정 기준은     
# 1. 경기시간 > 2. 대회 우선순위(TBD) > 3. 좌측팀 가나다순 

def open(url):
    try:
        context = ssl._create_unverified_context()
        html = urlopen(url, context=context)
        source = html.read()
        html.close()
    except HTTPError as e:
        err = e.read()
        errCode = e.getcode()
        print("HTTP ERROR >>> ", errCode)
    
    return BeautifulSoup(source, "html5lib")

def main():
    try:

        print(" == start == ")

        frame = TargetConfig.SPORTS

        # 오늘 경기
        now = datetime.today().strftime("%Y%m%d")
        NowUrl = frame + now
        soup = open(NowUrl)

        # 어제 경기
        # yest = (datetime.today() + timedelta(days=-1)).strftime("%Y%m%d")
        # yestUrl = frame + yest

        # 오늘 경기 : 현재 시간 이전으로 경기 검색
        time = datetime.today().strftime("%H")
        print("현재시간 >>> " + time)
        # <tr class="ing">, <td class="state">최종결과 입력 전 입니다</td> --> 제외
        scoreboard = soup.find("table", class_="tbl_scoreboard_day")
        for boardTime in soup.find_all("td", class_="time"):
            if time >= boardTime.get_text()[0:2]:
                print(boardTime.get_text()[0:2] + " ============ ")
                table = boardTime.find_next().find("table")
                trs = table.find_all("tr")
                for tr in trs[1:]:
                    print(tr["class"])
                    if not 'ing' in tr["class"]:
                        for state in tr.find_all("td", class_="state"):
                            score = state.get_text().replace('\n', " ").replace('\t', " ").replace("  ", "")
                            if not score.strip() == "최종결과 입력 전 입니다.":
                                print(score)
                        
    except:
        print("error2")


if __name__ == "__main__":

    try:
         main()
    except:
        print("error1")