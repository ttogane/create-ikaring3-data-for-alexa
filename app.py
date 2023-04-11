import json
import requests
import os
import boto3
from datetime import datetime
from enum import Enum

IKARING_SCHEDULE_API_URL = "https://spla3.yuu26.com/api"
ENVIRONMENT = "local" if os.getenv("ENVIRONMENT") == "local" else "prod"
USER_AGENT = os.getenv("USER_AGENT")
BATTLE_SCHEDULE_TABLE = "splatoon3-battle-schedules"

class BattleType(Enum):
  REGULAR = "レギュラーマッチ"
  CHALLENGE = "バンカラマッチ(チャレンジ)"
  OPEN = "バンカラマッチ(オープン)"
  X = "Xマッチ"
  FEST = "フェスマッチ"

''' マッチタイプを返却する '''
def get_battle_type(battle_type):
  if battle_type == "bankara_challenge":
      return BattleType.CHALLENGE.value
  elif battle_type == "bankara_open":
      return BattleType.OPEN.value
  elif battle_type == "x":
      return BattleType.X.value
  elif battle_type == "fest":
      return BattleType.FEST.value
  else:
      return BattleType.REGULAR.value

''' ルールのスケジュールをフォーマットする '''
def rule_schedules(schedules, battle_type):
  rule_schedules = []
  battle = get_battle_type(battle_type)

  for schedule in schedules[battle_type]:
    start_time = datetime.strptime(schedule["start_time"], "%Y-%m-%dT%H:%M:%S%z").timestamp()
    end_time = datetime.strptime(schedule["end_time"], "%Y-%m-%dT%H:%M:%S%z").timestamp()
    is_fest = schedule["is_fest"]
    rule = schedule["rule"]["name"] if not(is_fest) else BattleType.FEST.value
    stages = schedule["stages"]
    for stage in stages:
      stage_name = stage["name"]
      image = stage["image"]
      rule_schedules.append(
        {
          "start_time": int(start_time),
          "end_time": int(end_time),
          "battle_type": battle,
          "rule": rule,
          "stage": stage_name,
          "image": image
        }
      )
    if is_fest and schedule["is_tricolor"]:
      rule_schedules.append(
        {
          "start_time": int(start_time),
          "end_time": int(end_time),
          "battle_type": battle,
          "rule": "トリカラバトル",
          "stage": schedule["tricolor_stage"]["name"],
          "image": schedule["tricolor_stage"]["image"]
        }
      )
  return rule_schedules

''' 全ルールのスケジュールをDynamo書き込み用にフォーマットとする '''
def format_battle_schedules(battle_schedules):
  result = battle_schedules["result"]
  fest = []
  regular = []
  bankara_challenge = []
  bankara_open =[]
  x =[]

  if result["regular"][0]["is_fest"]:
    fest =rule_schedules(result, "fest")
  else:
    regular = rule_schedules(result, "regular")
    bankara_challenge = rule_schedules(result, "bankara_challenge")
    bankara_open = rule_schedules(result, "bankara_open")
    x = rule_schedules(result, "x")

  return [*regular, *bankara_challenge, *bankara_open, *x, *fest]

''' DynamoDBにデータを書き込む '''
def insert_to_dynamodb(table, data):
  dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table(table)
  try:
    with table.batch_writer(overwrite_by_pkeys=["stage", "start_time"]) as batch:
      for d in data:
        batch.put_item(
            Item = d
        )
  except Exception as error:
    raise error


def handler( event, context ):

  battle_schedules = {}
  parttime_job_schedules = {} # TODO:バイトスケジュールを追加する
  if ENVIRONMENT == "local":
    with open('data/fest_schedules.json') as fp:
        battle_schedules = json.load(fp)
    
    # with open('data/parttime_job_schedules.json') as fp:
    #     parttime_job_schedules = json.load(fp)

  elif ENVIRONMENT == "prod":
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json;charset=utf-8"
        }
    api_response = requests.get(IKARING_SCHEDULE_API_URL + "/schedule", headers = headers)
    battle_schedules = json.loads(api_response.text)

    # api_response = requests.get(IKARING_SCHEDULE_API_URL + "/coop-grouping/schedule", headers = headers)
    # parttime_job_schedules = json.loads(api_response.text)
  
  insert_data = format_battle_schedules(battle_schedules)
  insert_to_dynamodb(BATTLE_SCHEDULE_TABLE, insert_data)

  return json.dumps({"message": "OK"})