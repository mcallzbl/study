# 学习记录

缓存b站收藏夹是用来自动将指定用户收藏夹中全部内容缓存到本地的脚本<br>
还在完善中，不支持多线程下载<br>
参考https://github.com/SocialSisterYi/bilibili-API-collect<br>
requests tqdm库需要自行安装<br>
pip install requests<br>
pip install tqdm<br>

### 需要自行安装符合你系统版本的ffmpeg并添加到环境变量
若为linux可能会不支持flv<br>
找到以下行代码并将flv改为mp4即可解决<br>
videoFile = os.path.join(videoPath,f"{filename}.flv")
