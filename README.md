python-doubanfm
===============

python 豆瓣FM 命令行客户端

启动服务：

    fm -s

开始播放：

	fm -p

下一首：

    fm -n

暂停/继续：

    fm -G

当前歌曲：

    fm -i

喜欢：

    fm -f

不喜欢：

    fm -u

退出：

    fm -x


可以用 Firebug 导出 firefox 的 cookie 到 ~/.cache/python-doubanfm/cookies.txt
这样就可以用 喜欢/不喜欢 的功能了

配置文件的路径为 ~/.config/python-doubanfm/doubanfm.conf ，
可以在其中配置其他的播放源，比如 本地歌曲(localrandom)

#### 依赖关系

需要安装 gstreamer，以及 gstreamer 用于播放 MP3 的插件，
还有 python 对于 gstreamer 的包装库， python-gst

在 [Debian](http://www.debian.org/) 中需要执行如下命令：

	sudo apt-get install gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly
	sudo apt-get install python-gst0.10
