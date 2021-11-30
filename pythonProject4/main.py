import requests
import time
import json
from tqdm import tqdm
from collections import deque

from pymongo import MongoClient

api_key = "***********************"
startUser = "NCCPEfKUnjBHseDFg4MEBlOUdHvGsHmCtPVThjNrpe1K9ZtXt_QjnO6m3G4ewOCRgUskRUaxUE-m6A"

request_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
    "Accept-Language": "ko,en-US;q=0.9,en;q=0.8,es;q=0.7",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": api_key
}
client = MongoClient('localhost', 27017)
db = client.riot
cnt = 0


def match_v5_get_list_match_id(puuid, start, count):
    while (True):
        try:
            url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
            r = requests.get(url, headers=request_header)
            time.sleep(1)

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

            if r.status_code == 200:
                return r.json()
            else:
                return None

        except:
            print("오류 발생")
            return


def match_v5_get_info_match(matchid):
    while (True):
        try:
            url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{matchid}"

            r = requests.get(url, headers=request_header)
            time.sleep(1)

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
            if r.status_code == 200:
                return r.json()
            else:
                return None

        except:
            print("오류 발생")
            return


def writeDB(json_data):
    try:
        matchId = json_data['metadata']['matchId']
        games = db.games
        games.insert_one(json_data)
        global cnt
        print(cnt)
        cnt += 1

    except KeyError:
        return


def dbHasMatch(key):
    games = db.games
    result = games.find_one({'metadata.matchId': key})

    if result is None:
        return False
    return True


def dbHasUser(key):
    checkCol = db.checkCol
    result = checkCol.find({"key": key})
    result = list(result)
    if (len(result) > 0):
        return True
    else:
        return False


def insertKeyDB(key):
    checkCol = db.checkCol
    checkCol.insert_one({"key": key})


r = match_v5_get_list_match_id(startUser, 0, 100)

matchQueue = deque(r)

cnt = 0
try:
    while len(matchQueue) > 0:

        cur_game = matchQueue.popleft()
        game_info = match_v5_get_info_match(cur_game)

        if game_info is None:
            continue

        for i in range(10):
            tmpUserId = game_info['info']['participants'][i]['puuid']

            if dbHasUser(tmpUserId) is False:

                match_list = match_v5_get_list_match_id(tmpUserId, 0, 100)
                for match in match_list:
                    if dbHasMatch(match) is False:
                        matchQueue.append(match)

                insertKeyDB(tmpUserId)

        if game_info['info']['gameMode'] == 'ARAM':
            writeDB(game_info)

        while len(matchQueue) > 500:
            save_game_info = match_v5_get_info_match(matchQueue.pop())

            if (len(matchQueue) % 5) == 0:
                continue
            if save_game_info is None or save_game_info['info']['gameMode'] != 'ARAM':
                continue
            writeDB(save_game_info)


except KeyboardInterrupt:
    print("종료중 입니다...")
    checkCol = db.checkCol
    with tqdm(total=len(matchQueue)) as pbar:
        while (len(matchQueue) > 0):
            save_game_info = matchQueue.pop()

            checkCol.delete_one({'key': save_game_info})
            pbar.update(1)

finally:
    print("종료되었습니다")
