import requests
from tqdm import tqdm
import os
import logging
import configparser
import json
import re
from moviepy.editor import VideoFileClip, AudioFileClip
import stat

cookies = {'cookie':'YourCookie'}
uid = 0

script_path = os.path.abspath(__file__)
current_directory = os.path.dirname(script_path)
log_file_path = os.path.join(current_directory, '缓存日志.log')
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
    config_file = os.path.join(current_directory, 'DownLoadFavconfig.ini')
    if not os.path.exists(config_file):
        default_config = configparser.RawConfigParser()
        print("请输入您的uid:",end="")
        uid  = input()
        print("请输入您的cookies(似乎用私密模式获得的效果更好):",end="")
        cookies['cookie'] = input()
        default_config['user'] = {
            'uid': uid,
            'cookies': cookies['cookie']
        }
        with open(config_file, 'w') as file:
            default_config.write(file)
        print("您的配置文件存储在：",config_file)
        logging.info("配置文件写入完成")
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file)
    if config.has_section('user'):
        uid = int(config.get('user', 'uid'))
        cookies['cookie'] = config.get('user', 'cookies')
        logging.info("配置读取成功!")
        print("配置读取成功!")
    else:
        print("配置文件中缺少 'user' 部分，请检查配置文件格式。")
        logging.warning("配置文件错误！")

#获取全部收藏夹
def getFavor()->str:
    print("正在读取您的收藏夹")
    logging.info("读取收藏夹...")
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all'
    params = {'up_mid': uid}
    response = requests.get(url, cookies = cookies,params=params)
    if response.status_code == 200:
        print("读取全部收藏夹成功！")
        logging.info("读取全部收藏夹成功！")
        return response.text
    else:
        print(f'获取失败，状态码：{response.status_code}')
        logging.warning(f'获取失败，状态码：{response.status_code}')
        return 'error'
    
#获取收藏夹内视频信息 
def analysisFavorites(response_data):
    logging.info("开始分析收藏夹")
    print("开始分析收藏夹...")
    data_dict = json.loads(response_data)
    data_list = data_dict["data"]["list"]
    for item in data_list:
        title = item['title']
        print("正在分析:",title)
        getVideoByDir(item["id"],dir=title)
    print("b站收藏夹分析完成！")
    logging.info("b站收藏夹分析完成！")

#获取收藏夹下视频的bvid，并获取视频详细信息
def getVideoByDir(media_id,dir):
    params = {'media_id': media_id}
    url = 'https://api.bilibili.com/x/v3/fav/resource/ids'
    response = requests.get(url, cookies = cookies,params=params)
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
    response = requests.get(url,cookies=cookies,params=params)
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
        getUrlByCid(bvid,item['cid'],filename=filename,dir=filePath)

#通过cid获取视频和音频文件的下载链接
def getUrlByCid(bvid,cid,filename,dir):
    params = {'bvid': bvid,'cid':cid,'qn':0,'fnval':80,'fnver':0,'fourk':1}
    # 设置要请求的URL
    url = 'https://api.bilibili.com/x/player/playurl'
    response = requests.get(url, cookies = cookies,params=params)
    data_dict = json.loads(response.text)
    datas = data_dict["data"]
    dashs = datas['dash']
    videoUrls = dashs['video']
    videoUrl = videoUrls[0]['baseUrl']
    audioUrls = dashs['audio']
    audioUrl = audioUrls[0]['baseUrl']
    download_file(videoUrl,"video.m4s",filename)
    download_file(audioUrl,"audio.m4s",filename)
    videoPath = current_directory+'\\'+dir
    if not os.path.exists(videoPath):
        os.makedirs(videoPath)
        folder_stat = os.stat(videoPath)
        os.chmod(videoPath, folder_stat.st_mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH)
    print("开始合并文件")
    videoFile = videoPath+'\\'+clean_filename(filename)+'.flv'
    video_clip = VideoFileClip(os.path.join(current_directory,"video.m4s"))
    audio_clip = AudioFileClip(os.path.join(current_directory,"audio.m4s"))
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(videoFile, codec="flv")
    audio_clip.close()
    print("视频合并完成!")
    logging.info(f"{filename}下载完成")

# 下载文件
def download_file(url, filename,realName):
    headers = {
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
    'referer': 'https://www.bilibili.com'
    }
    response = requests.get(url,cookies,headers=headers)
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
            except requests.exceptions.ChunkedEncodingError:
                logging.warning(f"{realName}下载出错")

        print(filename,'下载完成')
    else:
        print(f'请求失败，状态码：{response.status_code}')
        logging.warning(f"{realName}下载出错")
    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)    

#清理文件名中非法字符
def clean_filename(filename):
    pattern = r'[<>:"/\\|?*]'
    cleaned_filename = re.sub(pattern, '', filename)
    return cleaned_filename
        

def main():
    print("程序启动")
    logging.info("程序启动")
    initConfig()
    favList = getFavor()
    if favList!='error':
       analysisFavorites(favList)

main()