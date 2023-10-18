import requests
from tqdm import tqdm
import os
import logging
import configparser
import json
import re
import subprocess
import sys

cookies = {'cookie':'YourCookie'}
uid = 0
script_path = os.path.abspath(__file__)
current_directory = os.path.dirname(script_path)
log_file_path = os.path.join(current_directory, '缓存日志.log')
config_file = os.path.join(current_directory, 'DownLoadFavconfig.ini')
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def initConfig():
    print("开始初始化配置...")
    logging.info("开始初始化配置")
    global uid,cookies
    if not os.path.exists(config_file):
        updateConfig()
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file)
    if config.has_section('user'):
        uid = int(config.get('user', 'uid'))
        cookies['cookie'] = config.get('user', 'cookies')
        logging.info("配置读取成功!")
        print("配置读取成功!")
    else:
        print("配置文件中缺少 'user' 部分，请检查配置文件格式。")
        logging.ERROR("配置文件错误！")
        updateConfig()

#更新配置文件
def updateConfig():
    default_config = configparser.RawConfigParser()
    while True:
        uid  = input("请输入您的uid:")
        if uid.isdigit():
            break
        else:
            print("请输入正确的uid!")
    cookies['cookie'] = input("请输入您的cookies(似乎用私密模式获得的更持久):")
    default_config['user'] = {
        'uid': uid,
        'cookies': cookies['cookie']
    }
    with open(config_file, 'w') as file:
        default_config.write(file)
    print("您的配置文件存储在：",config_file)
    logging.info("配置文件写入完成")

#获取全部收藏夹
def getFavor()->str:
    print("正在读取您的收藏夹")
    logging.info("读取收藏夹...")
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all'
    params = {'up_mid': uid}
    response = doGetRequest(url,params=params)
    if response.status_code == 200:
        print("读取全部收藏夹成功！")
        logging.info("读取全部收藏夹成功！")
        return response.text
    else:
        print(f'获取失败，状态码：{response.status_code}')
        logging.warning(f'获取失败，状态码：{response.status_code}')
        return 'error'

#做get请求
def doGetRequest(url, params=None, **kwargs):
    try:
        return requests.get(url, cookies = cookies,params=params)
    except Exception as e:
        logging.warning(str(e))
        return None
    
#根据'-'返回需要下载的收藏夹任务列表    
def findHyphen(string,max)->list:
    count = string.count('-')
    if count==0:
        if int(string)<=max:
            return [string]
        return None
    elif count == 1:
        list = []
        strlist = string.split('-')
        numlist = [int(num) for num in strlist]
        index = numlist[0]
        if index>max|numlist[1]>max:
            return None
        while index<=numlist[1]:
            list.append(index)
            index = index+1
        return list
    return None

#展示收藏夹 
def showFavorites(response_data):
    data_dict = json.loads(response_data)
    data_list = data_dict["data"]["list"]
    for index, item in enumerate(data_list):
        title = item['title']
        media_count = item['media_count']
        print(f"|{index+1}|{title}|{media_count}个视频")
    tasks = set()
    while True:
        line = input("请输入你想要缓存的收藏夹前的编号(不同编号之间请用逗号分隔，也可用\"-\"表示连续的多个编号)\n").strip()
        if re.search(r'[^0-9,-]',line):
            print("请输入合法的编号！")
        else:
            numbers = line.split(',')
            for number in numbers:
                numlist = findHyphen(number,len(data_list))
                if numlist!=None:
                    for task in numlist:
                        tasks.add(task)
            break
    for task in tasks:
        #print(tasks)
        executeDownload(data_list[int(task)-1])
#执行下载任务
def executeDownload(favouriteList):
    title = favouriteList['title']
    print("正在缓存收藏夹：",title)
    getVideoByDir(favouriteList["id"],dir=title)

#获取收藏夹下视频的bvid，并获取视频详细信息
def getVideoByDir(media_id,dir):
    params = {'media_id': media_id}
    url = 'https://api.bilibili.com/x/v3/fav/resource/ids'
    response = doGetRequest(url,params=params)
    data_dict = json.loads(response.text)
    data_list = data_dict["data"]
    for item in data_list:
        try:
            getVideoDetail(item['bvid'],dir=dir)
        except Exception as e:
            error_message = str(e)
            logging.warning("获取视频详情失败(大概率是视频失效了)")
            logging.warning(error_message)

#获取视频的详细信息
def getVideoDetail(bvid,dir):
    params = {'bvid': bvid}
    url = 'https://api.bilibili.com/x/web-interface/view'
    response = doGetRequest(url,params=params)
    if response.status_code == 200:
        data_dict = json.loads(response.text)
        datas = data_dict["data"]
        pages = datas['pages']
        for item in pages:
            filename = ''
            filePath = ''
            if datas['videos']>1:
                filePath = dir+'/'+datas["title"]
                filename = item['part']
            else:
                filePath = dir
                filename = datas["title"]
            filename = clean_filename(filename)
            getUrlByCid(bvid,item['cid'],filename,filePath)
    else:
        print("获取视频详细信息失败")
        logging.error("获取视频详细信息失败")
    

#通过cid获取视频和音频文件的下载链接
def getUrlByCid(bvid,cid,filename,dir):
    params = {'bvid': bvid,'cid':cid,'qn':127,'fnval':1040,'fnver':0,'fourk':1}
    # 设置要请求的URL
    url = 'https://api.bilibili.com/x/player/playurl'
    response = doGetRequest(url,params=params)
    if response.status_code == 200:
        data_dict = json.loads(response.text)
        datas = data_dict["data"]
        dashs = datas['dash']
        videoUrls = dashs['video']
        videoUrl = videoUrls[0]['baseUrl']
        audioUrls = dashs['audio']
        audioUrl = audioUrls[0]['baseUrl']
        download_file(videoUrl,"video.m4s",filename)
        download_file(audioUrl,"audio.m4s",filename)
        videoPath = os.path.join(current_directory,dir)
        if not os.path.exists(videoPath):
            os.makedirs(videoPath)
        mergeVideo(videoPath,filename)
        logging.info(f"{filename}下载完成!")
    else:
        print("获取下载链接失败")
        logging.error(f"{filename}获取下载链接失败")

#将视频文件和音频文件合并
def mergeVideo(videoPath,filename):
    print("合并文件...")
    videoFile = os.path.join(videoPath,f"{filename}.mp4")
    command = ['ffmpeg',
                '-i', os.path.join(current_directory, "video.m4s"),
                '-i', os.path.join(current_directory, "audio.m4s"), 
                '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental','-y', '-v', 'error',videoFile]
    try:
        subprocess.run(command, check=True)
        os.remove(os.path.join(current_directory, "video.m4s"))
        os.remove(os.path.join(current_directory, "audio.m4s"))
        print("合并完成!")
    except Exception as e:
        error_message = str(e)
        print("合并过程中出现错误:", error_message)
        logging.warning(f"{filename}合并出错!")
        logging.error(error_message)

# 下载文件
def download_file(url, filename,realname):
    headers = {
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
    'referer': 'https://www.bilibili.com'
    }
    response = requests.get(url,headers=headers, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        file_path = os.path.join(current_directory, filename)
        with open(file_path, 'wb') as file, tqdm(
            desc='下载进度',
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            try:
                for data in response.iter_content(chunk_size=1024):
                    progress_bar.update(len(data))
                    file.write(data)
            except Exception as e:
                error_message = str(e)
                logging.warning(f"{realname}下载出错")
                logging.error(error_message)
        print(realname,'下载完成')
    else:
        print(f'请求失败，状态码：{response.status_code}')
        logging.error(f"{realname}下载出错")

#清理文件名中非法字符
def clean_filename(filename):
    pattern = r'[<>:"/\\|?*]'
    cleaned_filename = re.sub(pattern, '', filename)
    return cleaned_filename

#开始缓存
def startDownload():
    favList = getFavor()
    if favList!='error':
       showFavorites(favList)
#退出程序
def exitProgram():
    print("程序停止运行，欢迎下次光临！")
    logging.info("程序中止运行")
    sys.exit(0)
#指令名称
orderName = {
    '1':"更新配置",
    '2':"开始缓存",
    '3':"显示指令",
    '4':"退出程序"
}
#输出指令列表
def printHelp():
    for instruction, description in orderName.items():
        print(f"| {instruction} | {description} |")

#指令集
order = {
    '1':updateConfig,
    '2':startDownload,
    '3':printHelp,
    '4':exitProgram
}
#程序入口
def main():
    print("程序启动")
    logging.info("程序启动")
    initConfig()
    printHelp()
    while True:
        line = input("输入指令前的数字:")
        if line not in order:
            print("请输入正确的指令！")
        else:
            order[line]()

main()
