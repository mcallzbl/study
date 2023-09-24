# git学习

### 配置⽤户信息
 git config --global user.name "name" <br>
 git config --global user.email "email"<br>

### 配置⽂本编辑器
git config --global core.editor vim

### 初始化仓库
git init

### 克隆远程目录
git clone url

### 查看文件状态
git status [filename]<br>
git status （查看全部文件状态）

### 添加到暂存区
git add filename

### 提交
git commit -m [message]或<br>
git commit [filename] -m [message]

### 远程仓库管理
ssh-keygen -m PEM -t rsa -b 4096<br>
\#-m PEM：指定了生成的密钥的格式为PEM（Privacy-Enhanced Mail）格式存储。<br>
\#-t rsa：指定了要生成的密钥的类型将是RSA<br>
-b 4096：指定了密钥的比特长度为4096位<br>
\# 在~/.ssh/⽬录中会⽣成⼀对密钥⽂件<br>
\# 其中id_rsa为私钥，id_rsa.pub为公钥<br>
\# 输出公钥⽂件的内容
cat ~/.ssh/id_rsa.pub

将公钥上传至github或gitee中


git remote add origin <url><br> 命令添加远程仓库地址， origin 为远程仓库的别名

git push -u origin master<br> 命令将本地仓库推送⾄远程仓库， -u 参数表⽰将本地与<br>
远程关联起来，以后要推送更新的代码，只需执⾏ git push 即可

git pull 获取远端更新

### 获取帮助
git --help

### git分支
git branch 列出本地所有分支

git branch -r 列出远程所有分支

git branch name<br> 建立新的分支并停留在原分支

git checkout -b [branch]<br> 新建分支并切换到新的分支

git checkout [branch]<br>
切换分支

git merge [branch]<br>
合并分支到当前分支

git branch -d [branch-name] <br>
删除分支

git push origin --delete  remoteBranchName <br>
删除远程分支


