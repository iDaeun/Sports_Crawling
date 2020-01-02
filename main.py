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

def DBInsert(conn, curs, order, time, name, result):
    print(order, time, name, result)
    sql = 'INSERT INTO SPORTS (G_ORDER, C_TIME, G_TIME, G_NAME, G_RESULT) VALUES(%s, now(), %s, %s, %s) ON DUPLICATE KEY UPDATE G_TIME = %s, G_NAME = %s, G_RESULT = %s'
    data = (order, time, name, result, time, name, result)
    curs.execute(sql, data)
    conn.commit()
    print("** 데이터 입력 **\n")

def findGame(soup, needed, gameDate, conn, curs, count):
    scoreboard = soup.find("table", class_="tbl_scoreboard_day")

    for gameName in soup.find_all("td", class_="game"):
        for i in range(0, len(needed)):
            if needed[i] == gameName.get_text():
                # 본인 tr + 본 게임에 해당되는 다른 tr들 가져오기
                thisClass = gameName.find_previous("tr")
                tr = thisClass.find_all("tr")[1] 
                if not 'ing' in tr["class"]:
                    for state in tr.find_all("td", class_="state"):
                        score0 = getScore(state)
                        if score0 is not None:
                            count +=1
                            DBInsert(conn, curs, count, gameDate, needed[i], score0)
                
                        for o in tr.find_all_next("tr"):
                            if o.get("class") == None:
                                continue
                            elif 'start' in o.get("class"):
                                break
                            else:
                                if 'state' in o.find_next("td").get("class"):
                                    for state1 in o.find_all("td", class_="state"):
                                        score1 = getScore(state1)
                                        if score1 is not None:
                                            count +=1
                                            DBInsert(conn, curs, count, gameDate, needed[i], score1)
                print("----------------------------------")
    
    return count

def getScore(state):
    score = state.get_text().replace('\n', " ").replace('\t', " ").replace("  ", "")
    if not score.strip() == "최종결과 입력 전 입니다." and 'vs' not in score.strip():
        #print(score)
        return score

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

def main(logger):
    try:

        count = 0

        # DB
        conn = pymysql.connect(host=TargetConfig.DB_HOST, user=TargetConfig.DB_USER, password=TargetConfig.DB_PW, db=TargetConfig.DB_NAME, charset='utf8')
        curs = conn.cursor()
        print("== start == ")

        frame = TargetConfig.SPORTS

        # 대회 우선 순위 : MLB, 프리미어리그, 라리가, 리그앙, 프리미어12, K리그1, 남자프로배구, 여자프로배구, 프로농구, 여자프로농구
        needed = ['MLB', '프리미어리그', '라리가', '리그앙', '프리미어12', 'K리그1', '남자프로배구', '여자프로배구', '프로농구', '여자프로농구']

        # 오늘 경기
        today = datetime.today().strftime("%Y%m%d")
        todUrl = frame + today
        soup = open(todUrl)

        gameDate = datetime.today().strftime("%m.%d")
        count = findGame(soup, needed, gameDate, conn, curs, count)

        # 어제 경기
        yest = (datetime.today() + timedelta(days=-1)).strftime("%Y%m%d")
        yestUrl = frame + yest
        soup1 = open(yestUrl)

        gameDate = (datetime.today() + timedelta(days=-1)).strftime("%m.%d")

        findGame(soup1, needed, gameDate, conn, curs, count)
                        
    except Exception as ex:
        logger.error("error2 " + str(ex))
        print("error2")


if __name__ == "__main__":

    logging.basicConfig(format='[%(lineno)d]%(asctime)s||%(message)s')
    logger = logging.getLogger(name="myLogger")

    try:
         main(logger)
    except:
        print("error1")