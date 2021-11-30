import requests
import time
from collections import deque
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pymysql


cred = credentials.Certificate('sw-project-53154-firebase-adminsdk-26ska-1234173cfd.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://sw-project-53154-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

api_key = "RGAPI-bbbada61-7f5a-48dd-94c4-5cd37d2db851"
startUser = "9OyGO37nOAwusEmqr66RfjOTQ9lcZTxtUfiU4TsHMRERGT3H7JwsCpww0pjQdpqRlZfKP6VEVClpSg"

request_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
    "Accept-Language": "ko,en-US;q=0.9,en;q=0.8,es;q=0.7",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": api_key
}
conn = pymysql.connect(
    host = "192.168.30.3",
    port = 3300,
    user = "root",
    password = "hisac0330",
    database = "riot",
    charset = 'utf8'
)
curs = conn.cursor()

def match_v5_get_list_match_id(puuid, start, count):
    while (True):
        try:
            url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
            r = requests.get(url, headers=request_header)

            if (r.status_code == 429):
                print('api cost full : From puuid, infinite loop start')
                # print('loop location : ',i)
                start_time = time.time()

                while True:  # 429error가 끝날 때까지 무한 루프
                    if r.status_code == 429:

                        print('try 10 second wait time')
                        time.sleep(10)

                        r = requests.get(url, headers=request_header)
                        print(r.status_code)

                    elif r.status_code == 200:  # 다시 response 200이면 loop escape
                        print('total wait time : ', time.time() - start_time)
                        print('recovery api cost')
                        break

            return r.json()
        except:
            print("오류 발생")
            time.sleep(30)


def match_v5_get_info_match(matchid):
    while (True):
        try:
            url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{matchid}"

            r = requests.get(url, headers=request_header)

            if (r.status_code == 429):
                print('api cost full : From match, infinite loop start')
                # print('loop location : ',i)
                start_time = time.time()

                while True:  # 429error가 끝날 때까지 무한 루프
                    if r.status_code == 429:

                        print('try 10 second wait time')
                        time.sleep(10)

                        r = requests.get(url, headers=request_header)
                        print(r.status_code)

                    elif r.status_code == 200:  # 다시 response 200이면 loop escape
                        print('total wait time : ', time.time() - start_time)
                        print('recovery api cost')
                        break
                    else:
                        print("치명적인 오류 발생")
                        exit(-1)
            return r.json()
        except:
            print("오류 발생")
            time.sleep(30)


def writeDB(json_data):
    try:
        sql = '''INSERT INTO `game`(`name`, `jsoncol`) VALUES ("json_object", json_object(json_data));'''
        curs.execute(sql)
    except KeyError:
        return


def checkDB(key):
    return False


def insertKeyDB(key):
    return True


r = match_v5_get_list_match_id(startUser, 0, 100)
# r = r.json() #소환사의 고유 id

matchQueue = deque(r)

# dictGameId = dict()
# dictUserId = dict()

# for i in r:
#    dictUserId[i]=True

cnt = 0
try:
    while (len(matchQueue) > 0):

        cur_game = matchQueue.popleft()
        game_info = match_v5_get_info_match(cur_game)

        if (game_info['info']['gameMode'] != 'ARAM'):
            continue

        for i in range(10):
            tmpUserId = game_info['info']['participants'][i]['puuid']

            if (checkDB(tmpUserId) != True):

                match_list = match_v5_get_list_match_id(tmpUserId, 0, 100)
                for i in match_list:
                    if (checkDB(i) != True):
                        matchQueue.append(i)
                        insertKeyDB(i)
                insertKeyDB(tmpUserId)
                time.sleep(1)

        writeDB(game_info)

        while (len(matchQueue) > 500):
            save_game_info = match_v5_get_info_match(matchQueue.pop())
            writeDB(save_game_info)

            print(cnt)
            cnt += 1
            time.sleep(1)
except KeyboardInterrupt:
    print("종료중 입니다...")
    while (len(matchQueue) > 0):
        save_game_info = match_v5_get_info_match(matchQueue.pop())
        writeDB(save_game_info)

        print(cnt)
        cnt += 1
        time.sleep(1)
finally:
    print("종료되었습니다")