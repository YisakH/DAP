from pymongo import MongoClient
from tqdm import tqdm
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import json

client = MongoClient('localhost', 27017)
db = client.riot

check = db['checkCol']
games = db.games

all_games = games.find()
all_check = check.find()


def coldelete():
    for i in tqdm(all_check, desc="check col deleting...", mininterval=0.01, ncols=10):
        key = i['key']
        if (len(key) > 15):
            check.delete_many({'key': key})
        else:
            query_result = games.find_one({'metadata.matchId': key})
            if (query_result is None):
                check.delete_many({'key': key})


def colinsert():
    for i in tqdm(all_games, desc="check col inserting...", mininterval=0.01):
        key = i['metadata']['matchId']

        # query = db.find({'checkCol.key:{'})
        query = check.find_one({'key': key})

        if query is None:
            check.insert_one({'key': key})
            # print(key + ' 삭제 완료')

    # for i in tqdm(all_games):


def dbHasMatch(key):
    check = db.dupes
    result = check.find_one({'matchId': key})

    if result is None:
        return False
    return True


def insert(key):
    check = db.dupes
    check.insert_one({'matchId': key})


def dupMatchDel():
    every_games = db.games.find()
    global cnt
    for game in tqdm(every_games, desc="duplicated games deleting..."):
        key = game['metadata']['matchId']
        uid = game['_id']

        if dbHasMatch(key):
            db.games.delete_one({"_id": uid})
            cnt += 1
        else:
            insert(key)


def selectDataRecordz():
    every_games = db.games.find()
    selectedDataUser = db.selectedDataSortedUser
    for game in tqdm(every_games, desc="selecting data"):
        key = {
            "matchId": game['metadata']['matchId'],
            "win": game['info']['teams'][0]['win']
        }
        key2 = {
            "matchId": game['metadata']['matchId'],
            "win": not game['info']['teams'][0]['win']
        }


        bli = []
        rli = []
        for i in range(0, 5):
            bli.append(game['info']['participants'][i]['championName'])

        bli.sort()
        for i in range(0, 5):
            key['b' + str(i)] = bli[i]

        for i in range(0, 5):
            key2['r' + str(i)] = bli[i]
        
        for i in range(5, 10):
            rli.append(game['info']['participants'][i]['championName'])
        rli.sort()
        for i in range(5, 10):
            key['r' + str(i-5)] = rli[i-5]

        for i in range(5, 10):
            key2['b' + str(i-5)] = rli[i-5]

        selectedDataUser.insert_one(key)
        selectedDataUser.insert_one(key2)


def selectDataNoShake():
    every_games = db.games.find()
    selectedDataUser = db.selectedDataSortedUser
    for game in tqdm(every_games, desc="selecting data"):
        key = {
            "matchId": game['metadata']['matchId'],
            "win": game['info']['teams'][0]['win']
        }

        bli = []
        rli = []
        for i in range(0, 5):
            bli.append(game['info']['participants'][i]['championName'])

        bli.sort()
        for i in range(0, 5):
            key['b' + str(i)] = bli[i]

        for i in range(5, 10):
            rli.append(game['info']['participants'][i]['championName'])
        rli.sort()
        for i in range(5, 10):
            key['r' + str(i - 5)] = rli[i - 5]

        selectedDataUser.insert_one(key)

def makeChampionCode():
    every_games = db.games.find()
    chamCode = db.champCode
    cnt = 1
    champList = set()
    for game in tqdm(every_games, desc="making champ code"):
        for i in range(0, 10):
            champList.add(game['info']['participants'][i]['championName'])
    print(len(champList))

    champList = list(champList)
    champList.sort()
    champDict = dict()

    for champ in champList:
        champDict[champ] = cnt
        cnt += 1

    with open ('./champCode.json', 'w', encoding='utf-8') as file:
        json.dump(champDict, file, indent='\t')

def labelEncoding():
    filename = './'
    data = pd.read_csv(filename)

    df = data.drop(['matchId', '_id'], axis=1)
    df.head()

    x = df.iloc[:, :-1]
    champList = x.to_numpy().flatten()
    champList = set(champList.tolist())
    champList = list(champList)

    le = LabelEncoder()
    encode = le.fit(champList)

    encode.transform(['Jayce', 'Lux', 'Graves'])

def selectData():
    userInfo = db.userInfo
    every_games = db.games.find()

    for game in tqdm(every_games):
        for user in game['participants']:
            data = dict()
            data['summonerId'] = user['summonerId']


# 챔피언 clustering에 사용할 numerical 데이터 추출 함수
def champClassification():
    every_games = db.games.find()
    champInfo = db.champInfo
    for game in tqdm(every_games):
        for i, user in enumerate(game['info']['participants']):
            try:
                data = {
                    'championName': user['championName'],
                    'kills': user['kills'],
                    'deaths': user['deaths'],
                    'assists': user['assists'],
                    'damageDealtToTurrets': user['damageDealtToTurrets'],
                    'doubleKills': user['doubleKills'],
                    'damageSelfMitigated': user['damageSelfMitigated'],
                    'goldEarned': user['goldEarned'],
                    'killingSprees': user['killingSprees'],
                    'largestCriticalStrike': user['largestCriticalStrike'],
                    'longestTimeSpentLiving': user['longestTimeSpentLiving'],
                    'magicDamageDealtToChampions': user['magicDamageDealtToChampions'],
                    'physicalDamageDealtToChampions': user['physicalDamageDealtToChampions'],
                    'timeCCingOthers': user['timeCCingOthers'],
                    'timePlayed': user['timePlayed'],
                    'totalDamageDealt': user['totalDamageDealt'],
                    'totalDamageDealtToChampions': user['totalDamageDealtToChampions'],
                    'totalDamageShieldedOnTeammates': user['totalDamageShieldedOnTeammates'],
                    'totalDamageTaken': user['totalDamageTaken'],
                    'totalHeal': user['totalHeal'],
                    'trueDamageDealtToChampions': user['trueDamageDealtToChampions'],
                    'totalHealsOnTeammates': user['totalHealsOnTeammates'],
                    'totalTimeCCDealt': user['totalTimeCCDealt'],
                    'win': user['win']
                }
            except:
                print(game['info']['gameId'], user['championName'])
                exit(-1)

            champInfo.insert_one(data)

# No use
def champClassification2():
    every_games = db.games.find()
    champInfo = db.champInfo
    for game in tqdm(every_games):
        for i, user in enumerate(game['info']['participants']):
            champInfo.insert_one(user)

# 챔피언 이름 -> 챔피언 코드 인코딩(매핑) 함수
def encoding():
    with open('./champCode.json', 'r') as f:
        code = json.load(f)
        print(code)

        games = db.selectedDataSortedUser.find()
        encodedresult = db.encodedChamp

        for game in tqdm(games):
            bindex = list('b' + str(i) for i in range(1, 159))
            bdata = [False for i in range(158)]
            rindex = list('r' + str(i) for i in range(1, 159))
            rdata = [False for i in range(158)]

            for i in range(5):
                champName = game['b' + str(i)]
                bdata[code[champName]] = True

            for i in range(5):
                champName = game['r' + str(i)]
                rdata[code[champName]] = True

            dict1 = dict(zip(bindex, bdata))
            dict2 = dict(zip(rindex, rdata))

            dict1.update(dict2)
            dict1['win'] = game['win']

            encodedresult.insert_one(dict1)


with open('./champCode.json', 'r') as f:
    code = json.load(f)

    game = {'b0':'Rakan','b1' : 'Ivern', 'b2' : 'Janna', 'b3':'Lulu', 'b4':'Nami', 'r0':'Ahri','r1' : 'Akali', 'r2' : 'Ashe', 'r3':'Camille', 'r4':'Gnar'}
    bindex = list('b' + str(i) for i in range(1, 159))
    bdata = [False for i in range(158)]
    rindex = list('r' + str(i) for i in range(1, 159))
    rdata = [False for i in range(158)]

    for i in range(5):
        champName = game['b' + str(i)]
        bdata[code[champName]] = True

    for i in range(5):
        champName = game['r' + str(i)]
        rdata[code[champName]] = True

    dict1 = dict(zip(bindex, bdata))
    dict2 = dict(zip(rindex, rdata))

    dict1.update(dict2)

    print(dict1)
