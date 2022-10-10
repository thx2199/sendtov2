from datetime import date, datetime, timedelta
import math,requests,os,random,re,json
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d") #今天的日期
start_date = '2022-10-09'
aim_date = '01-22'
city = os.getenv('CITY')
app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')
user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')
name = os.getenv('NAME')


def get_english():
    """获取金山词霸每日一句，英文和翻译"""
    url = "http://open.iciba.com/dsapi/"
    r = requests.get(url, timeout=100)
    note = r.json()['content'] + "\n" + r.json()['note']
    return note

def get_weather():
    url = "http://autodev.openspeech.cn/csp/api/v2.1/weather?openId=aiuicus&clientType=android&sign=android&city=" + city
    res = requests.get(url, timeout=100).json()
    today = res['data']['list'][0]
    tomor = res['data']['list'][1]
    if tomor['weather'] == '阴':
        text =  city + "明天是个阴天喔，气温是"
    elif tomor['weather'][-1] == '雨':
        text =  city + "明天有" + tomor['weather'] + "，" + name + "外出时记得携带雨具！气温是"
    else: text =  city + "明天是" + tomor['weather'] + "天喔，气温是"
    text = text + str(int(tomor['low'])) + '~' + str(int(tomor['high'])) + "℃，空气质量" + str(tomor['airQuality']) + "，空气湿度" + today['humidity'] + "，会呼呼地吹" + today['wind'] + "。"
    urlh = 'http://timor.tech/api/holiday/tts/tomorrow'
    resh = requests.get(urlh, timeout=100).json()
    holiday = "\n\n休息日的话.." + resh['tts']
    return text + holiday

# 获取当前日期为星期几
def get_week_day():
  week_list = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
  week_day = week_list[datetime.date(today).weekday()]
  return week_day

# 推送天数
def get_memorial_days_count():
  delta = today - datetime.strptime(start_date, "%Y-%m-%d")
  return delta.days

# 春节倒计时
def get_counter_left(aim_date):
  # 为了经常填错日期的同学
  if re.match(r'^\d{1,2}\-\d{1,2}$', aim_date):
    next = datetime.strptime(str(date.today().year) + "-" + aim_date, "%Y-%m-%d")
  elif re.match(r'^\d{2,4}\-\d{1,2}\-\d{1,2}$', aim_date):
    next = datetime.strptime(aim_date, "%Y-%m-%d")
    next = next.replace(nowtime.year)
  else: return '日期错乱掉了..'
  if next < nowtime:
    next = next.replace(year=next.year + 1)
  return '距离春节还有 ' + str((next - today).days) + ' 天。'

# 接口不稳定，所以失败的话会重新调用，直到成功
def get_words():
  # OpenRefactory Warning: The 'requests.get' method does not use any 'timeout' threshold which may cause program to hang indefinitely.
  words = requests.get("https://api.shadiao.pro/chp", timeout=100)
  if words.status_code != 200:
    return get_words()
  return words.json()['data']['text']

def format_temperature(temperature):
  return math.floor(temperature)

# 随机颜色
def get_random_color():
  return "#%06x" % random.randint(0, 0xFFFFFF)

# 返回一个数组，循环产生变量
def split_date():
  return aim_date.split('\n')

#aimtime = 
andtime = '今天是推送的第'+ str(get_memorial_days_count()) + '天，' + get_counter_left(aim_date) 

data = {
  "date": {
    "value": today.strftime('%Y年%m月%d日'),
    "color": get_random_color()
  },
  "week_day": {
    "value": get_week_day(),
    "color": get_random_color()
  },
  "weather": {
    "value": get_weather(),
    "color": get_random_color()
  },
  "note": {
    "value": get_english(),
    "color": get_random_color()
  },
  "love_days": {
    "value": andtime,
    "color": get_random_color()
  },
  "words": {
    "value": get_words(),
    "color": get_random_color()
  },
}

if __name__ == '__main__':
  try:
    client = WeChatClient(app_id, app_secret)
  except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

  wm = WeChatMessage(client)
  try:
    for user_id in user_ids:
      print('正在发送给 %s, 数据如下：%s' % (user_id, data))
      res = wm.send_template(user_id, template_id, data)
  except WeChatClientException as e:
    print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
    exit(502)

    #{{note.DATA}}  {{weather.DATA}}  {{love_days.DATA}} {{words.DATA}}
