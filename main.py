import re
import sys
import time
import json
import random
import pystray
import threading
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPalette, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PIL import Image
from pyncm import apis


class MyWidget(QWidget):
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
        self.music_id = 0
        self.CurrentMusicTime = 0
        self.CurrentLrcList_ori = []
        self.CurrentLrcList_tran = []
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
        self.Lrc_fo.setGeometry(0, 0, 1000, 500)
        self.Lrc_fo.setFont(font)
        self.Lrc_fo.setPalette(palette)
        self.Lrc_ch.setVisible(False)
        # 为歌曲名创建一个定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(800)  # 800ms
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.update_text)
        self.timer3 = QTimer()
        # 使用pystray创建托盘图标
        self.menu = pystray.Menu(
            pystray.MenuItem("添加到歌单", self.add_to_playlist),
            pystray.MenuItem("编辑配置文件", self.edit_config),
            pystray.MenuItem("退出", self.quit_app)
        )
        self.image = Image.open("icon.png")
        self.icon = pystray.Icon("example", self.image, "Example App", self.menu)
        # TODO:恢复下条
        # apis.login.LoginViaCellphone()

    def add_to_playlist(self):
        st = apis.playlist.SetManipulatePlaylistTracks([str(self.music_id)], 5334895570, op='add')
        if st['code'] == 200:
            print("ok")
        elif st['code'] == 502:
            print("已有该歌曲")
        else:
            print(st)
        pass

    def edit_config(self):
        self.SongName.setVisible(True)
        self.Lrc_ch.setVisible(False)
        pass

    def quit_app(self):
        self.SongName.setVisible(False)
        self.Lrc_ch.setVisible(True)
        pass

    @staticmethod
    def lrc_make(lrc: str) -> tuple[int, str]:
        lrc = lrc.split(']')
        lrc_time_all = lrc[0][1:].split(':')
        # 获取时间戳
        lrc_time_strap = float(lrc_time_all[0]) * 60 * 1000 + float(lrc_time_all[1]) * 1000
        lrc_name = lrc[1]
        return int(lrc_time_strap), lrc_name
        pass

    def drawLrc_(self, text_):
        self.pixmap = QPixmap(400, 100)
        self.pixmap.fill(Qt.transparent)
        self.painter = QPainter(self.pixmap)
        self.painter.setFont(self.Lrc_ch.font())
        self.painter.setPen(self.Lrc_ch.palette().color(QPalette.WindowText))
        self.painter.drawText(self.pixmap.rect(), Qt.AlignLeft, text_)
        self.painter.end()
        self.Lrc_ch.setPixmap(self.pixmap)

    def drawLrc(self):
        cur_name = self.text
        cur_time = self.timex()
        lrc_list_ = []
        # 计算时间偏移值，也就是当前应该播放的地方
        offset = self.timex_c(self.CurrentMusicTime, cur_time)
        # 预处理歌词
        for itm in self.CurrentLrcList_ori:
            if len(itm) >= 10:
                lrc_list_.append(self.lrc_make(itm))
        lrc_list_time = self.lrc_index([itm[0] for itm in lrc_list_], offset)
        # 得到位置，开始渲染
        for itm in range(lrc_list_time[0], len(lrc_list_)):
            if self.text != cur_name:
                break
            self.drawLrc_(lrc_list_[itm][1])
            time.sleep((lrc_list_[itm + 1][0] - lrc_list_[itm][0]) / 1000)
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

    def _update_display(self):
        # 读取JSON文件
        with open("C:\\Users\\pk5ls\\AppData\\Local\\Netease\\CloudMusic\\webdata\\file\\history", "r",
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
            self.CurrentLrcList_ori = apis.track.GetTrackLyrics(str(self.music_id))['lrc']['lyric'].split('\n')
            self.CurrentLrcList_tran = apis.track.GetTrackLyrics(str(self.music_id))['tlyric']['lyric'].split('\n')
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
    app = QApplication(sys.argv)
    w = MyWidget()
    w.setWindowFlags(w.windowFlags() | Qt.WindowStaysOnTopHint)
    w.show()
    w.icon.run()
    sys.exit(app.exec_())
    # TODO:检测暂停
    # TODO:双语歌词
    # TODO:优化歌词消息
    # TODO:空白消息过滤
