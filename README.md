python-doubanfm
===============

python 豆瓣FM 命令行客户端

需要安装 pyglet 和 AVbin
在 debian 里可以使用如下命令：

    sudo apt-get install python-pyglet
    sudo apt-get install libavbin0

启动服务：
    ./fm.py -s 1>/dev/null 2>&1 &
下一首：
    ./fm.py -n
暂停/继续：
    ./fm.py -G
当前歌曲：
    ./fm.py -i
喜欢：
    ./fm.py -l
不喜欢：
    ./fm.py -u
退出：
    ./fm.py -x

可以用 Firecookie 导出 firefox 的 cookie 到 ~/.cache/python-doubanfm/cookies.txt
这样就可以用 喜欢/不喜欢 的功能了
