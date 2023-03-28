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
        self.music_id = 0
        self.setGeometry(1400, -190, 1000, 500)
        # self.setGeometry(1452, -227, 1000, 500)  # 设置窗口位置和大小
        self.setWindowFlags(
            Qt.Window | Qt.CustomizeWindowHint | Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 设置窗口背景透明
        # 用于记录鼠标按下时的坐标
        self.drag_pos = QPoint()
        # 创建一个QLabel控件用于显示文字
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 0, 1000, 500)
        # 创建一个QFont对象，设置字体属性
        font = QFont()
        font.setFamily('等线')
        font.setPointSize(12)
        font.setBold(True)
        # 初始化文字
        self.text = "Default Text"
        self.text_ = ''
        self.label.setFont(font)
        palette = QPalette()
        palette.setColor(QPalette.WindowText, Qt.white)
        self.label.setPalette(palette)
        # 创建一个定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(800)  # 800ms
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.update_text)
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
        print("Edit config")
        pass

    def quit_app(self):
        print("qqq")
        sys.exit()

    def update_text(self, text):
        self.pixmap = QPixmap(400, 100)
        self.pixmap.fill(Qt.transparent)
        self.painter = QPainter(self.pixmap)
        self.painter.setFont(self.label.font())
        self.painter.setPen(self.label.palette().color(QPalette.WindowText))
        self.painter.drawText(self.pixmap.rect(), Qt.AlignLeft, text)
        self.painter.end()
        self.label.setPixmap(self.pixmap)

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
            # 渲染文字为QPixmap
            print(len(self.text))
            self.text_ = self.text
            self.update_text(self.text)
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
