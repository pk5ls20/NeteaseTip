import os
import re
import sys
import time
import json
import queue
import random
import signal
import logging
import pystray
import threading
from PIL import Image
from pyncm import apis
from win10toast import ToastNotifier
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPalette, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QLabel, QWidget


class NotificationThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.notification_queue = queue.Queue()
        self.app = QApplication.instance()
        self.win = ToastNotifier()

    def run(self):
        while True:
            try:
                title, message = self.notification_queue.get()
            except queue.Empty:
                continue
            print(f'发出桌面通知: {title} {message}')
            self.win.show_toast(title, message, duration=3, threaded=True)
            time.sleep(5)

    def show_notification(self, title, message):
        self.notification_queue.put((title, message))


def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError as e:
            logging.error(f"IndexError: {e}")
            pass
        except FileNotFoundError as e:
            notification_thread.show_notification("NeteaseTip", f"文件不存在！{e}")
            logging.error(f"FileNotFoundError: {e}")
        except Exception as e:
            notification_thread.show_notification("NeteaseTip", f"出现未知异常！{e}")
            logging.error(f"Exception: {e}")

    return wrapper


class MyWidget(QWidget):
    @handle_exception
    def __init__(self):
        super().__init__()
        self.rand = lambda: random.randint(-10000, 10000)
        self.timex = lambda: int(time.time() * 1000)
        self.timex_c_sec = lambda x, y: abs(x - y) / 1000
        self.timex_c = lambda x, y: abs(x - y)
        self.lrc_do = lambda lrc: (
            int(lrc[1:].split(':')[0]) * 60 * 1000 + int(lrc[1:].split(':')[1]) * 1000, lrc.split(']')[1])
        self.lrc_index = lambda lst, num: (max([i for i in range(len(lst)) if lst[i] < num], default=None),
                                           min([i for i in range(len(lst)) if lst[i] > num], default=None))
        self.match_timecode = lambda s: bool(re.match(r'\d{2}:\d{2}.\d{2}(.\d{1,3})?', s))
        self.music_id = 0
        self.CurrentMusicTime = 0
        self.CurrentLrcList_ori = []
        self.CurrentLrcList_tran = []
        self.CurrentDoLrcDict = {}
        self.setGeometry(1400, -190, 1000, 500)
        # self.setGeometry(1452, -227, 1000, 500)  # 设置窗口位置和大小
        self.setWindowFlags(
            Qt.Window | Qt.CustomizeWindowHint | Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 设置窗口背景透明
        # 用于记录鼠标按下时的坐标
        self.drag_pos = QPoint()
        # 创建一个QLabel控件用于显示文字
        self.SongName = QLabel(self)
        self.SongName.setAlignment(Qt.AlignCenter)
        self.SongName.setGeometry(0, 0, 1000, 500)
        # 创建一个QFont对象，设置字体属性
        font = QFont()
        font.setFamily('等线')
        font.setPointSize(12)
        font.setBold(True)
        # 初始化文字
        self.text = "Default Text"
        self.text_ = ''
        self.SongName.setFont(font)
        palette = QPalette()
        palette.setColor(QPalette.WindowText, Qt.white)
        self.SongName.setPalette(palette)
        # 重复以上过程
        self.Lrc_ch = QLabel(self)
        self.Lrc_ch.setAlignment(Qt.AlignCenter)
        self.Lrc_ch.setGeometry(0, 0, 1000, 500)
        self.Lrc_ch.setFont(font)
        self.Lrc_ch.setPalette(palette)
        self.Lrc_fo = QLabel(self)
        self.Lrc_fo.setAlignment(Qt.AlignCenter)
        self.Lrc_fo.setGeometry(0, 0, 1000, 550)
        self.Lrc_fo.setFont(font)
        self.Lrc_fo.setPalette(palette)
        self.Lrc_ch.setVisible(False)
        self.Lrc_fo.setVisible(False)
        # 为歌曲名创建一个定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(800)  # 800ms
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.update_text)
        self.dp = 0
        # 使用pystray创建托盘图标
        self.menu = pystray.Menu(
            pystray.MenuItem("添加到歌单", self.add_to_playlist),
            pystray.MenuItem("切换歌曲/歌词", self.display),
            pystray.MenuItem("编辑配置文件", self.edit_config),
            pystray.MenuItem("退出", lambda: os.kill(os.getpid(), signal.SIGTERM))
        )
        self.image = Image.open("icon.png")
        self.icon = pystray.Icon("example", self.image, "Example App", self.menu)
        try:
            with open(f"{os.environ['APPDATA']}\\.neteasetip", "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except FileNotFoundError as e:
            notification_thread.show_notification("NeteaseTip", f"未能加载配置文件！{e}")
        # TODO:恢复下条
        try:
            apis.login.LoginViaCellphone(phone=self.config["phone"], passwordHash=self.config["passwordHash"])
            pass
        except Exception as e:
            notification_thread.show_notification("NeteaseTip", f"登陆失败，无法使用添加歌单功能！{e}")

    def add_to_playlist(self):
        st = apis.playlist.SetManipulatePlaylistTracks([str(self.music_id)], 5334895570, op='add')
        if st['code'] == 200:
            notification_thread.show_notification("NeteaseTip", "添加到歌单成功！")
        elif st['code'] == 502:
            notification_thread.show_notification("NeteaseTip", "歌单已有该歌曲！")
        else:
            notification_thread.show_notification("NeteaseTip", f"添加失败！{st}")
        pass

    def display(self):
        if self.dp == 0:
            print(1)
            self.SongName.setVisible(False)
            self.Lrc_ch.setVisible(True)
            self.Lrc_fo.setVisible(True)
            self.dp = 1
        else:
            print(2)
            self.SongName.setVisible(True)
            self.Lrc_ch.setVisible(False)
            self.Lrc_fo.setVisible(False)
            self.dp = 0

    @staticmethod
    @handle_exception
    def edit_config():
        os.startfile(f"{os.environ['APPDATA']}\\.neteasetip")

    def lrc_make(self, ori: list, tran: list) -> dict[int, list[str]]:
        lyrics_dict = {}
        new = ori + tran if (len(tran) > 1 and tran[0] != '') else ori
        for line in new:
            if line == '':
                continue
            time_marker = line.split(']')[0] + ']'
            time_marker_num = time_marker[1:len(time_marker) - 1]
            if not self.match_timecode(time_marker_num):
                continue
            time_marker_ = int(float(time_marker_num.split(':')[0]) * 60 * 1000
                               + float(time_marker_num.split(':')[1]) * 1000)
            lyrics = line[len(time_marker):]
            if time_marker_ in lyrics_dict:
                lyrics_dict[time_marker_][2] = lyrics
            else:
                if len(lyrics) > 1:
                    lyrics_dict[time_marker_] = [time_marker_, lyrics, '']
        return lyrics_dict

    def create_pixmap(self, text):
        pixmap = QPixmap(400, 100)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setFont(self.Lrc_ch.font())
        painter.setPen(self.Lrc_ch.palette().color(QPalette.WindowText))
        painter.drawText(pixmap.rect(), Qt.AlignLeft, text)
        painter.end()
        return pixmap

    def drawLrc_(self, text1, text2):
        pixmap1 = self.create_pixmap(text1)
        self.Lrc_ch.setPixmap(pixmap1)
        pixmap2 = self.create_pixmap(text2)
        self.Lrc_fo.setPixmap(pixmap2)

    def drawLrc(self):
        cur_name = self.text
        cur_time = self.timex()
        # 计算时间偏移值，也就是当前应该播放的地方
        self.CurrentDoLrcDict = self.lrc_make(self.CurrentLrcList_ori, self.CurrentLrcList_tran)
        dic = [int(self.CurrentDoLrcDict[key][0]) for key in self.CurrentDoLrcDict]
        offset = self.timex_c(self.CurrentMusicTime, cur_time + 2000)
        lrc_list_time = self.lrc_index([self.CurrentDoLrcDict[key][0] for key in self.CurrentDoLrcDict], offset)
        # 得到位置，开始渲染
        for itm in range(lrc_list_time[0], len(self.CurrentDoLrcDict)):
            if self.text != cur_name:
                break
            self.drawLrc_(self.CurrentDoLrcDict[dic[itm]][1], self.CurrentDoLrcDict[dic[itm]][2])
            time.sleep((dic[itm + 1] - dic[itm]) / 1000)
            pass
        # 根据时间偏移值选择当前歌词
        pass

    def update_text(self, text):
        self.pixmap = QPixmap(400, 100)
        self.pixmap.fill(Qt.transparent)
        self.painter = QPainter(self.pixmap)
        self.painter.setFont(self.SongName.font())
        self.painter.setPen(self.SongName.palette().color(QPalette.WindowText))
        self.painter.drawText(self.pixmap.rect(), Qt.AlignLeft, text)
        self.painter.end()
        self.SongName.setPixmap(self.pixmap)

    @handle_exception
    def _update_display(self):
        # 读取JSON文件
        with open(f"{os.environ['APPDATA'][:-8]}\\Local\\Netease\\CloudMusic\\webdata\\file\\history", "r",
                  encoding="utf-8") as f:
            data = json.loads(f.read())
        # 检查a[0]是否有变化
        if f"{data[0]['track']['name']} - {data[0]['track']['artists'][0]['name']}" != self.text:
            # 更新文字
            self.text = f"{data[0]['track']['name']} - {data[0]['track']['artists'][0]['name']}"
            self.music_id = data[0]['track']['id']
            print(len(self.text))
            self.text_ = self.text
            self.update_text(self.text)
            # 加入歌词
            self.CurrentMusicTime = data[0]['time']
            try:
                self.CurrentLrcList_ori = apis.track.GetTrackLyrics(str(self.music_id))['lrc']['lyric'].split('\n')
            except KeyError:
                self.CurrentLrcList_ori = []
            try:
                self.CurrentLrcList_tran = apis.track.GetTrackLyrics(str(self.music_id))['tlyric']['lyric'].split('\n')
            except KeyError:
                self.CurrentLrcList_tran = []
            self.drawLrc()
        else:
            if len(self.text) > 30:
                self.text_ = self.text_[1:] + self.text_[0]
                print(self.text_)
                self.update_text(self.text_)
            else:
                pass
        print("ok")

    def update_display(self):
        threading.Thread(target=self._update_display).start()
        pass

    def mousePressEvent(self, event):
        # 鼠标左键按下时记录当前坐标
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        # 移动窗口
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        # 鼠标左键释放时清除记录的坐标
        if event.button() == Qt.LeftButton:
            self.drag_pos = QPoint()


if __name__ == '__main__':
    notification_thread = NotificationThread()
    notification_thread.start()
    app = QApplication(sys.argv)
    w = MyWidget()
    w.setWindowFlags(w.windowFlags() | Qt.WindowStaysOnTopHint)
    w.show()
    w.icon.run()
    sys.exit(app.exec_())
    # TODO:检测暂停 - 放弃
    # TODO:优化歌词消息
    # TODO:歌词滚动 - 放弃
