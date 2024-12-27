import sys
import os
import json
import shutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit, QVBoxLayout, QWidget, QStatusBar, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImageReader
from PyQt5.QtCore import Qt, QEvent, QRect
from PyQt5.QtMultimedia import QSound
import html
import pyperclip
import pvsubfunc

# 引数取得
args = sys.argv

# アプリ名称
WINDOW_TITLE = "Prompt Viewer"
# 設定ファイル
SETTINGS_FILE = "PromptViewer_settings.json"
# 設定ファイルのキー名
IMAGE_FCOPY_DIR = "image-fcopy-dir"
IMAGE_FMOVE_DIR = "image-fmove-dir"
SOUND_BEEP = "sound-beep"
SOUND_FCOPY_OK = "sound-fcopy-ok"
SOUND_FMOVE_OK = "sound-fmove-ok"
SOUND_F_CANSEL = "sound-f-cansel"
SOUND_MOVE_TOP = "sound-move-top"
SOUND_MOVE_END = "sound-move-end"
INFO_LABEL_W = "info-label-w"
GEOMETRY_X = "geometry-x"
GEOMETRY_Y = "geometry-y"
GEOMETRY_W = "geometry-w"
GEOMETRY_H = "geometry-h"

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def closeEvent(self, event):
        """ウィンドウを閉じる際に設定を保存"""
        self.save_settings()
        super().closeEvent(event)

    def initUI(self):
        self.imageFileCopyDir = ""
        self.imageFileMoveDir = ""
        self.soundBeep = ""
        self.soundFileCopyOK = ""
        self.soundFileMoveOK = ""
        self.soundFileCansel = ""
        self.soundMoveTop = ""
        self.soundMoveEnd = ""
        self.infoLabelWidth = 480
        self.filetype = -1     #-1:no comment, 0:org jpg 1:sd1111 or forge png, 2:comfyUI png, 3:other file

        self.NewLine = '\u2029'
        self.pydir = os.path.dirname(os.path.abspath(__file__))
        self.setWindowTitle(WINDOW_TITLE)
        self.setStyleSheet("background-color: black;")

        self.setGeometry(0, 0, 600, 640)    #位置とサイズ
        self.setMinimumSize(320 + self.infoLabelWidth, 320)      #最小サイズ（兼デフォルトサイズ）
        #設定ファイルが存在しない場合初期値で作成する
        if not os.path.exists(SETTINGS_FILE):
            self.createSettingFile()
        # 起動時にウィンドウ設定を復元
        self.load_settings()

        # メインウィジェットとレイアウト
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.layout = QHBoxLayout(self.centralWidget)   #横並びレイアウトに変更
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 画像表示用ラベル
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.imageLabel)

        # 情報表示用ラベル
        self.infoTextEdit = QTextEdit()
        font = self.infoTextEdit.font()
        #デフォルトはArial。他にMeiryo UI、Times New Roman、Symbol、メイリオ、Comic Sans MS
        #等幅フォント一覧：BIZ UDゴシック、BIZ UD明朝、HGｺﾞｼｯｸE、HGｺﾞｼｯｸM、MS Gothic、ＭＳ 明朝
        font.setFamily('MS Gothic')
        self.infoTextEdit.setFont(font)
        self.infoTextEdit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.5);
                color: #006699;
                font-size: 13px;
                border: 1px solid #444444;
            }
        """)
        self.infoTextEdit.setFixedWidth(self.infoLabelWidth)  # 横幅固定
        #self.infoTextEdit.setEnabled(False)    #操作不能、選択も不可
        self.infoTextEdit.setReadOnly(True)     #リードオンリー、選択やコピーは可能
        self.infoTextEdit.installEventFilter(self)
        self.layout.addWidget(self.infoTextEdit)

        # ステータスバー
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("color: white; font-size: 14px; background-color: #31363b;")
        self.setStatusBar(self.statusBar)
        self.showStatusBarMes("drop image file or dir")

        # 現在の画像ファイル
        self.currentImage = None
        self.imageFolder = None
        self.imageFiles = []
        self.fullscreen = False
        self.fitscreen = -1
        self.imageWidth = 0
        self.imageHeight = 0
        self.screenWidth = self.width()
        self.screenHeight = self.height()
        self.infoPrompt = ""
        self.infoNegaPrompt = ""
        self.infoHighResPrompt = ""
        self.infoSeed = ""

        # ドラッグ＆ドロップ有効化
        self.setAcceptDrops(True)

        # 画像を移動するための変数
        self.dragging = False
        self.last_pos = None

        # 引数にてファイルorフォルダ指定
        if len(args) > 1:
            self.loadFile(args[1])

    #設定ファイルの初期値作成
    def createSettingFile(self):
        pvsubfunc.write_value_to_config(SETTINGS_FILE, IMAGE_FCOPY_DIR, "W:/_temp/ai")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, IMAGE_FMOVE_DIR, "W:/_temp/ai2")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, SOUND_BEEP,      "PromptViewer_beep.wav")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, SOUND_FCOPY_OK,  "PromptViewer_filecopyok.wav")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, SOUND_FMOVE_OK,  "PromptViewer_filemoveok.wav")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, SOUND_F_CANSEL,  "PromptViewer_filecansel.wav")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, SOUND_MOVE_TOP,  "PromptViewer_movetop.wav")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, SOUND_MOVE_END,  "PromptViewer_moveend.wav")
        pvsubfunc.write_value_to_config(SETTINGS_FILE, INFO_LABEL_W, 480)
        self.save_settings()

    def load_settings(self):
        self.imageFileCopyDir = pvsubfunc.read_value_from_config(SETTINGS_FILE, IMAGE_FCOPY_DIR)
        self.imageFileMoveDir = pvsubfunc.read_value_from_config(SETTINGS_FILE, IMAGE_FMOVE_DIR)
        self.soundBeep = pvsubfunc.read_value_from_config(SETTINGS_FILE, SOUND_BEEP)
        self.soundFileCopyOK = pvsubfunc.read_value_from_config(SETTINGS_FILE, SOUND_FCOPY_OK)
        self.soundFileMoveOK = pvsubfunc.read_value_from_config(SETTINGS_FILE, SOUND_FMOVE_OK)
        self.soundFileCansel = pvsubfunc.read_value_from_config(SETTINGS_FILE, SOUND_F_CANSEL)
        self.soundMoveTop = pvsubfunc.read_value_from_config(SETTINGS_FILE, SOUND_MOVE_TOP)
        self.soundMoveEnd = pvsubfunc.read_value_from_config(SETTINGS_FILE, SOUND_MOVE_END)

        self.infoLabelWidth = pvsubfunc.read_value_from_config(SETTINGS_FILE, INFO_LABEL_W)
        #self.setGeometry(100, 200, 320, 480)    #位置とサイズ
        geox = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_X)
        geoy = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_Y)
        geow = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_W)
        geoh = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_H)
        if any(val is None for val in [geox, geoy, geow, geoh]):
            self.setGeometry(0, 0, 600, 640)    #位置とサイズ
        else:
            self.setGeometry(geox, geoy, geow, geoh)    #位置とサイズ

    def save_settings(self):
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_X, self.geometry().x())
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_Y, self.geometry().y())
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_W, self.geometry().width())
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_H, self.geometry().height())

    def exit(self) -> None:
            self.close()

    def loadImage(self, filePath):
        pixmap = QPixmap(filePath)
        if pixmap.isNull():
            self.showStatusBarMes("not supprt file.")
            self.play_wave(self.soundBeep)
            return  # 無効な画像の場合は処理しない
        self.currentImage = filePath
        self.imageFolder = os.path.dirname(filePath)
        self.imageFiles = sorted([f for f in os.listdir(self.imageFolder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        self.updateTitle()
        self.updateInfo()
        self.showStatusBarMes("image loaded.")

        # 画像のサイズをウィンドウに合わせて拡大縮小
        self.resizeImage()

    def updateTitle(self):
        if self.currentImage and self.imageFiles:
            currentIndex = self.imageFiles.index(os.path.basename(self.currentImage)) + 1
            totalFiles = len(self.imageFiles)
            filecountlen = len(str(totalFiles))
            pos = str(currentIndex).rjust(filecountlen, "0")
            fileName = os.path.join(self.imageFolder, os.path.basename(self.currentImage)).replace("\\", "/")
            wt = f"[{pos}/{totalFiles}] {fileName}"
        else:
            wt = WINDOW_TITLE
        self.setWindowTitle(wt)

    def showStatusBarMes(self, mes):
        self.statusBar.showMessage(f"{mes}")

    def showStatusBarErrorMes(self, mes):
        self.statusBar.showMessage(f"{mes}")
        self.play_wave(self.soundBeep)

    def initCopyInfo(self):
        self.infoSeed = ""
        self.infoPrompt = ""
        self.infoNegaPrompt = ""
        self.infoHighResPrompt = ""

    def addTextColorSD(self, comstr):
        comres = "Prompt: " + comstr
        #文字列部分の改行エスケープを消しておく
        comres = comres.replace("\"","")
        comres = comres.replace("\\n", "\n")

        #コピー可能なPrompt情報を退避
        res = pvsubfunc.extract_between(comres, "Seed: ", ", Size:")
        if res: self.infoSeed = str(res[0])
        res = pvsubfunc.extract_between(comres, "Prompt: ", "Negative prompt: ")
        if res:
            self.infoPrompt = pvsubfunc.normalize_newlines(res[0], os.linesep)
        res = pvsubfunc.extract_between(comres, "Negative prompt: ", "Steps: ")
        if res:
            self.infoNegaPrompt = pvsubfunc.normalize_newlines(res[0], os.linesep)
        res = pvsubfunc.extract_between(comres, "Hires prompt: ", ", Hires upscale: ")
        if res:
            self.infoHighResPrompt = pvsubfunc.normalize_newlines(res[0], os.linesep)


        #ウィジェット用のHTMLエスケープ、改行の加工
        comres = html.escape(pvsubfunc.normalize_newlines(comres, self.NewLine))
        #ウィジェット用に見やすくするための改行を追加
        if self.filetype == 1:      #-1:no comment, 0:org jpg 1:sd1111 or forge png, 2:comfyUI png, 3:other file
            comres = comres.replace("Negative prompt: ", self.NewLine+"Negative prompt: ")
            comres = comres.replace("Steps: ", self.NewLine+"Steps: ")
        comres = comres.replace("Hires prompt: ", self.NewLine+"Hires prompt: ")
        comres = comres.replace(", Hires upscale: ", self.NewLine+"Hires upscale: ")
        #promptを灰色に
        comres = pvsubfunc.insert_between_all(comres,
                                        "Prompt: ", "Negative prompt: ",
                                        "<span style='color: #CCCCCC;'>", "</span>")
        #negative promptを紫に
        comres = pvsubfunc.insert_between_all(comres,
                                        "Negative prompt: ", "Steps: ",
                                        "<span style='color: #CC4488;'>", "</span>")
        #hires promptを緑に
        comres = pvsubfunc.insert_between_all(comres,
                                        "Hires prompt: ", "Hires upscale: ",
                                        "<span style='color: #33CC00;'>", "</span>")
        #SEED番号の強調
        comres = pvsubfunc.insert_between_all(comres,
                                        "Seed: ", ", Size:",
                                        "<span style='color: #00FFFF; font-size: 14px;'><b>", "</b></span>")
        #Model名の強調
        comres = pvsubfunc.insert_between_all(comres,
                                        "Model: ", ", VAE",
                                        "<span style='color: #FF9900; font-size: 14px;'><b>", "</b></span>")
        #Lora部分の強調
        comres = pvsubfunc.insert_between_all(comres,
                                        "&lt;lora:", "&gt;",
                                        "<span style='color: #FFFF00; font-size: 14px;'><b>", "</b></span>")
        #各種強調表示
        for pword in {"ADetailer prompt", "Steps:", "steps:"}:
            comres = pvsubfunc.add_around_all(comres, pword, "<span style='color: #CC4400;'>", "</span>")

        return comres

    #T.B.D きちんと要素判定しないと、文字列の検索だけでは厳しい
    def addTextColorComfyUI(self, comstr):
        comres = comstr
        comres = comres.replace('\\"', '\"')
        comres = comres.replace('\\n', '\n')
        comres = pvsubfunc.normalize_newlines(comres, self.NewLine)
        #promptを灰色に
        comres = pvsubfunc.insert_between_all(comres,
                                        " {\"inputs\": {\"text\": \"", "\",",
                                        "<span style='color: #CCCCCC;'>", "</span>")
        #Lora部分の強調
        comres = pvsubfunc.insert_between_all(comres,
                                        "{\"lora_name\": \"", "\",",
                                        "<span style='color: #FFFF00; font-size: 14px;'><b>", "</b></span>")
        #各種強調表示
        for pword in {"seed:", "Steps:", "steps:"}:
            comres = pvsubfunc.add_around_all(comres, pword, "<span style='color: #CC4400;'>", "</span>")
        return comres

    def updateInfo(self):
        if not self.currentImage:   return
        pixmap = QPixmap(self.currentImage)
        width, height = pixmap.width(), pixmap.height()
        self.imageWidth, self.imageHeight = width, height
        reader = QImageReader(self.currentImage)
        #keys = reader.textKeys()    #keyの一覧を取得
        comment = "- None -"
        imgcomment = ""
        self.filetype = 1   #0:org jpg 1:sd1111 or forge png, 2:comfyUI png, 3:other file
        #ToDo:改行コードと先頭と終端の扱いがおかしい
        # jpgでは改行コードが￥￥nの￥nだけで改行してるのと文頭と文末に無駄なキャラがいる
        # pngではreader.textでキャリッジ・リターンが無視されている感じ？
        if self.currentImage.lower().endswith(('.jpg', '.jpeg', '.webp')):
            imgcomment = str(pvsubfunc.get_jpg_comment(self.currentImage))
            #自作の変換ツールを通したjpgをImageライブラリで読み込むと不要なバイトなどがあるので修正する
            #imgcomment = pvsubfunc.remove_jpg_comment_Exifbyte(imgcomment)
            self.filetype = 0   #0:jpg
        elif self.currentImage.lower().endswith(('.png')):
            imgcomment = str(reader.text("parameters"))
            self.filetype = 1   #1:sd1111 or forge png
            if not imgcomment:
                imgcomment = str(reader.text("prompt"))
                self.filetype = 2   #2:comfyUI png
            if not imgcomment:
                imgcomment = str(reader.text("Description"))
                self.filetype = 3   #3:other file
        if not imgcomment:
            self.filetype = -1   #-1:no comment

        # 情報を2種類のフォントで表示
        path_info = f"Path: {self.currentImage}"
        image_info = f"Size: {width}x{height}px"
        comment_info = f"{imgcomment}"

        self.initCopyInfo()

        #filetype   -1:no comment, 0:org jpg 1:sd1111 or forge png, 2:comfyUI png, 3:other file
        if self.filetype in {0, 1}:
            comment_info = self.addTextColorSD(comment_info)
        elif self.filetype in {2}:
            comment_info = self.addTextColorComfyUI(comment_info)
        else:
            comment_info = comment

        styled_info = f"<span style='color: #008080; font-size: 14px;'>{path_info}</span><br>"
        styled_info += f"<span style='color: #008000; font-size: 14px;'><b>{image_info}</b></span><br>"
        styled_info += comment_info
        self.infoTextEdit.setText(styled_info)

    def resizeImage(self):
        if self.currentImage:
            pixmap = QPixmap(self.currentImage)
            # 情報表示を考慮した拡大縮小を行う
            imgsize = self.size()
            if self.fullscreen == False:
                imgsize.setWidth(imgsize.width() - self.infoLabelWidth)
            self.imageLabel.setPixmap(pixmap.scaled(imgsize, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        self.resizeImage()  # ウィンドウサイズ変更時に画像をリサイズ
        super().resizeEvent(event)

    #画像サイズ変更トグル
    def toggleFitScreen(self, scale):
        if self.fullscreen:
            return  # 全画面表示中は無効
        if self.currentImage == "":
            return  # 画像がない場合も無効

        if self.fitscreen < 0:
            #通常モードからFitモードへ
            self.fitscreen = scale
            #現在のウインドウサイズを退避
            self.screenWidth, self.screenHeight = self.width(), self.height()
            lw, lh = self.imageWidth, self.imageHeight
            if self.fitscreen == 0:
                lw = int(lw / 2)
                lh = int(lh / 2)
            if self.fitscreen == 2:
                lw = lw * 2
                lh = lh * 2

            lw += self.infoLabelWidth
            self.resize(lw, lh + 24)
        else:
            #Fitモードから通常モードへ
            self.fitscreen = -1
            #元のウインドウサイズに復帰
            self.resize(self.screenWidth, self.screenHeight)

    #全画面切り替えトグル
    def toggleFullscreen(self):
        if self.fullscreen:
            self.showNormal()
            self.statusBar.show()
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
            self.infoTextEdit.setVisible(True)
        else:
            self.showFullScreen()
            self.statusBar.hide()
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.infoTextEdit.setVisible(False)
        self.show()     #ウィジェットが表示/非表示などを切り替える場合など
        #self.update()   #ウィジェットの内容を更新する場合など
        self.fullscreen = not self.fullscreen
        self.resizeImage()  # ウィンドウサイズ変更時に画像をリサイズ
        #処理完了を待ちたい場合
        #QApplication.processEvents()

    #次の画像
    def showNextImage(self):
        if self.currentImage and self.imageFiles:
            currentIndex = self.imageFiles.index(os.path.basename(self.currentImage))
            nextIndex = (currentIndex + 1) % len(self.imageFiles)
            self.loadImage(os.path.join(self.imageFolder, self.imageFiles[nextIndex]).replace("\\", "/"))
            if nextIndex == 0:
                self.showStatusBarMes("first file")
                self.play_wave(self.soundMoveTop)
            else:
                self.showStatusBarMes("")

    #前の画像
    def showPreviousImage(self):
        if self.currentImage and self.imageFiles:
            currentIndex = self.imageFiles.index(os.path.basename(self.currentImage))
            prevIndex = (currentIndex - 1) % len(self.imageFiles)
            self.loadImage(os.path.join(self.imageFolder, self.imageFiles[prevIndex]).replace("\\", "/"))
            if prevIndex == len(self.imageFiles)-1:
                self.showStatusBarMes("last file")
                self.play_wave(self.soundMoveEnd)
            else:
                self.showStatusBarMes("")

    # コピーバッファ系の処理
    def copyInfoSeed(self):
        if self.infoSeed:
            pyperclip.copy(self.infoSeed)
            self.showStatusBarMes("copied seed.")
        else:
            self.showStatusBarErrorMes("not support - copy seed.")
    def copyInfoPrompt(self):
        if self.infoPrompt:
            pyperclip.copy(pvsubfunc.normalize_newlines(self.infoPrompt, os.linesep))
            self.showStatusBarMes("copied prompt.")
        else:
            self.showStatusBarErrorMes("not support - copy prompt.")
    def copyInfoHighResPrompt(self):
        if self.infoHighResPrompt:
            pyperclip.copy(pvsubfunc.normalize_newlines(self.infoHighResPrompt, os.linesep))
            self.showStatusBarMes("copied highres prompt.")
        else:
            self.showStatusBarErrorMes("not support - copy highres prompt.")
    def copyInfoNegaPrompt(self):
        if self.infoNegaPrompt:
            pyperclip.copy(pvsubfunc.normalize_newlines(self.infoNegaPrompt, os.linesep))
            self.showStatusBarMes("copied negative prompt.")
        else:
            self.showStatusBarErrorMes("not support - copy negative prompt.")

    #コピー処理
    def copyImageFile(self, destdir):
        if self.currentImage and self.imageFiles:
            srcfile = self.currentImage
            #destdir = self.imageFileCopyDir
            if not os.path.isfile(srcfile):
                self.showStatusBarMes(f"not exist file [{srcfile}]")
                self.play_wave(self.soundBeep)
                return
            if not os.path.isdir(destdir):
                self.showStatusBarMes(f"not exist dir [{destdir}]")
                self.play_wave(self.soundBeep)
                return

            dest_file = os.path.join(destdir, os.path.basename(srcfile)).replace("\\", "/")

            # コピー先に同名のファイルがすでに存在していれば削除のみ実行
            if os.path.exists(dest_file):
                os.remove(dest_file)
                self.showStatusBarMes(f"copy cansel [{dest_file}]")
                self.play_wave(self.soundFileCansel)
                return

            shutil.copy2(srcfile, destdir)
            self.showStatusBarMes(f"copyed [{dest_file}]")
            self.play_wave(self.soundFileCopyOK)

    #ムーブ処理
    def moveImageFile(self):
        if self.currentImage and self.imageFiles:
            srcfile = self.currentImage
            destdir = self.imageFileMoveDir
            dest_file = os.path.join(destdir, os.path.basename(srcfile)).replace("\\", "/")

            if not os.path.isdir(destdir):
                self.showStatusBarMes(f"not exist dir [{destdir}]")
                self.play_wave(self.soundBeep)
                return

            #すでに対象ファイルがなく、移動先フォルダに存在する場合は元に戻す
            if not os.path.isfile(srcfile) and os.path.isfile(dest_file):
                shutil.copy2(dest_file, os.path.dirname(srcfile))
                os.remove(dest_file)
                self.showStatusBarMes(f"move cancel [{srcfile}]")
                self.play_wave(self.soundFileCansel)
                return

            #対象フォルダにコピー後、ソースとなるファイルは削除する
            shutil.copy2(srcfile, destdir)
            if (os.path.isfile(dest_file)):
                os.remove(srcfile)
            self.showStatusBarMes(f"moved [{dest_file}]")
            self.play_wave(self.soundFileMoveOK)

    def play_wave(self, file_name):
        file_path = os.path.join(self.pydir, file_name).replace("\\", "/")
        if not os.path.isfile(file_path): return
        sound = QSound(file_path)
        sound.play()
        while sound.isFinished() is False:
            app.processEvents()

    def loadFile(self, fname):
        if os.path.isfile(fname):
            self.loadImage(fname)
        elif os.path.isdir(fname):
            files = sorted([f for f in os.listdir(fname) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
            if len(files) > 0:
                self.loadImage(os.path.join(fname, files[0]).replace("\\", "/"))
            else:
                self.showStatusBarMes(f"no image files in this folder")
                self.play_wave(self.soundBeep)
        else:
            self.showStatusBarMes(f"not support file type")
            self.play_wave(self.soundBeep)


    #========================================
    #= キーイベント処理（QTextBoxにて消費される分）
    #= https://doc.qt.io/qt-5/qt.html#Key-enum
    #========================================
    # 【重要】カーソルキーなどはkeyPressEventに通知されません。ここに記載してください
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # カーソルキーの判定
            keyid = event.key()
            if keyid in {Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Enter, Qt.Key_Return}:
                if keyid == Qt.Key_Right:
                    self.showNextImage()        #次のイメージへ
                elif keyid == Qt.Key_Left:
                    self.showPreviousImage()    #前のイメージへ
                elif keyid in {Qt.Key_Enter, Qt.Key_Return}:
                    self.toggleFullscreen()     #全画面切り替え
                elif keyid == Qt.Key_Up:
                    self.copyImageFile(self.imageFileCopyDir)        #コピー処理
                elif keyid == Qt.Key_Down:
                    self.moveImageFile()        #ムーブ処理
                    #self.copyImageFile(self.imageFileMoveDir)        #コピー処理２（設定のムーブフォルダへコピー）
                    #self.showMinimized()        #ウィンドウを最小化
                    pass
                return True  # イベントをここで処理したとみなして消費
        return super().eventFilter(obj, event)

    #========================================
    #= キーイベント処理（通常）
    #= https://doc.qt.io/qt-5/qt.html#Key-enum
    #========================================
    def keyPressEvent(self, event):
        keyid = event.key()
        pvsubfunc.dbgprint(f"[DBG] keyid : {keyid}")
        #1/2倍表示
        if keyid == Qt.Key_0:
            self.toggleFitScreen(0)
        #等倍表示
        elif keyid in {Qt.Key_1, Qt.Key_F}:
            self.toggleFitScreen(1)
        #2倍表示
        elif keyid == Qt.Key_2:
            self.toggleFitScreen(2)
        #次のイメージへ
        elif keyid in {Qt.Key_D}:       #Qt.Key_RightはeventFilter()にて記載
            self.showNextImage()        #次のイメージへ
        #前のイメージへ
        elif keyid in {Qt.Key_A}:       #Qt.Key_LeftはeventFilter()にて記載
            self.showPreviousImage()    #前のイメージへ
        elif keyid == Qt.Key_K:   #copy seed
            self.copyInfoSeed()
        elif keyid == Qt.Key_P:   #copy prompt
            self.copyInfoPrompt()
        elif keyid == Qt.Key_N:   #copy negative prompt
            self.copyInfoNegaPrompt()
        elif keyid == Qt.Key_H:   #copy hires prompt
            self.copyInfoHighResPrompt()
        #ファイルのコピー処理
        elif keyid in {Qt.Key_W}:       #Qt.Key_UpはeventFilter()にて記載
            self.copyImageFile(self.imageFileCopyDir)   #コピー処理
        #ファイルのムーブ処理
        elif keyid in {Qt.Key_S}:       #Qt.Key_DownはeventFilter()にて記載
            self.moveImageFile()        #ムーブ処理
            #self.copyImageFile(self.imageFileMoveDir)        #コピー処理２（設定のムーブフォルダへコピー）
            #self.showMinimized()        #ウィンドウを最小化
        #全画面切り替え
        #Qt.Key_Enter, Qt.Key_ReturnはeventFilter()にて記載
        #elif keyid in {Qt.Key_Enter, Qt.Key_Return}:
        #    self.toggleFullscreen()
        #終了処理
        elif keyid in {Qt.Key_Escape, Qt.Key_Q, Qt.Key_Slash, Qt.Key_Backslash}:
            self.appexit()
        super().keyPressEvent(event)

    def appexit(self):
        #全画面を解除してから終了（変な画面サイズが保存されてしまうため）
        if self.fullscreen:
            self.toggleFullscreen()
        self.exit()

    #ダブルクリック時に全画面切り替え
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggleFullscreen()
        super().mouseDoubleClickEvent(event)

    #ホイールで前後ファイルに移動
    def wheelEvent(self, event):
        pvsubfunc.dbgprint(f"[DBG] mouse wheel : {event.angleDelta().y()}")
        if event.angleDelta().y() > 0:
            self.showPreviousImage()
        else:
            self.showNextImage()
        super().wheelEvent(event)

    #ドラッグエンター
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    #ドラッグドロップ
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            filePath = event.mimeData().urls()[0].toLocalFile()
            self.loadFile(filePath)

    def mousePressEvent(self, event):
        pvsubfunc.dbgprint(f"[DBG] mouse button : {event.button()}")
        if event.button() == Qt.LeftButton and not self.fullscreen:
            self.dragging = True
            self.last_pos = event.globalPos()
        elif event.button() == Qt.RightButton:
            self.copyImageFile(self.imageFileCopyDir)        #コピー処理

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.globalPos() - self.last_pos
            self.move(self.pos() + delta)
            self.last_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())
