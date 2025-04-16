import sys
import os
import json
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
    QWidget, QStatusBar,
)
from PyQt5.QtGui import QPixmap, QImageReader, QImage, QIcon, QMovie
from PyQt5.QtCore import Qt, QEvent, QRect, QByteArray, QSize
from PyQt5.QtMultimedia import QSound
import html
import pyperclip
import pvsubfunc
import sdfileUtility
from PIL import Image
import zipfile
import io, time

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
SUPPORT_EXT = (".png", ".jpg", ".jpeg", ".webp", ".avif")

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def closeEvent(self, event):
        #全画面を解除してから終了（変な画面サイズが保存されてしまうため）
        if self.fullscreen:
            self.toggleFullscreen()
        #情報表示をもとに戻してから終了
        if not self.showInfoText:
            self.toggleInfoText()
        #ウィンドウを閉じる際に設定を保存
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
        self.filetype = -1     #-1:no comment, 0:org jpg,webp,avif 1:sd1111 or forge png, 2:comfyUI png, 3:other file
        #zipファイル対応
        self.zip_fname = ""     #zipファイル名
        self.zip_data = None    #zipデータ
        self.zip_files = ""     #zip内の画像ファイルリスト
        self.zip_index = 0      #zip内の表示画像index

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

        #webp再生用QMovie
        self.webpmovie = None   # 画像表示でwebpだった場合のプレイヤー

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
        self.showInfoText = True

        # アプリ左上のアイコンを設定
        try:
            self.setWindowIcon(QIcon("res/PromptViewer.ico"))
        except Exception as e:
            print(e)

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
        geox = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_X)
        geoy = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_Y)
        geow = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_W)
        geoh = pvsubfunc.read_value_from_config(SETTINGS_FILE, GEOMETRY_H)
        if any(val is None for val in [geox, geoy, geow, geoh]):
            self.setGeometry(0, 0, 600, 640)    #位置とサイズ
        else:
            self.setGeometry(geox, geoy, geow, geoh)    #位置とサイズ
        self.setMinimumSize(320 + self.infoLabelWidth, 320)      #最小サイズ（兼デフォルトサイズ）

    def save_settings(self):
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_X, self.geometry().x())
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_Y, self.geometry().y())
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_W, self.geometry().width())
        pvsubfunc.write_value_to_config(SETTINGS_FILE, GEOMETRY_H, self.geometry().height())

    def exit(self) -> None:
            self.close()

    def loadImage(self, filePath):
        self.currentImage = ""
        pixmap = self.loadImageToQPixmapFromFile(filePath)
        if not pixmap:
            self.showStatusBarErrorMes("not supprt file.")
            return  # 無効な画像の場合は処理しない
        self.currentImage = filePath
        self.imageFolder = os.path.dirname(filePath)
        self.imageFiles = sorted([f for f in os.listdir(self.imageFolder) if f.lower().endswith(SUPPORT_EXT)])
        self.updateTitle()
        self.updateInfo()
        self.showStatusBarMes("image loaded.")

        self.stop_WEbpMovie()
        if self.currentImage.lower().endswith(".webp"):
            self.webpmovie = QMovie(self.currentImage)
            self.imageLabel.setMovie(self.webpmovie)
            self.webpmovie.setScaledSize(self.get_fit_size(QImageReader(self.currentImage).size(), self.centralWidget.size()))
            self.webpmovie.start()

        # 画像のサイズをウィンドウに合わせて拡大縮小
        self.resizeImage()

    def loadZipImage(self, index):
        self.currentImage = ""
        imgname = self.zip_files[index]
        pixmap = self.getPixmapFromZip(imgname)
        if not pixmap:
            self.showStatusBarErrorMes("not supprt file.")
            return  # 無効な画像の場合は処理しない
        self.currentImage = imgname
        self.zip_index = index
        self.updateTitle()
        self.updateInfo()
        self.showStatusBarMes("image loaded.")

        # 画像のサイズをウィンドウに合わせて拡大縮小
        self.resizeImage()

    def getPixmapFromZip(self, fname):
        pixmap = None
        with self.zip_data.open(fname) as file:
            imgdata = file.read()

        if fname.lower().endswith(".avif"):
            img = self.get_zip_Image(fname)
            img = img.convert("RGBA")  # Ensure the image is in RGBA format
            data = img.tobytes("raw", "RGBA")
            qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
        else:
            qimage = QImage()
            if qimage.loadFromData(imgdata):
                pixmap = QPixmap.fromImage(qimage)

        return pixmap

    def updateTitle(self):
        wt = WINDOW_TITLE
        if self.zip_data:
            currentIndex = self.zip_index + 1
            totalFiles = len(self.zip_files)
            filecountlen = len(str(totalFiles))
            pos = str(currentIndex).rjust(filecountlen, "0")
            imagefilename = self.currentImage
            if self.zip_data:
                imagefilename = self.zipstringdecode(self.currentImage)
            fileName = f"{self.zip_fname} : {imagefilename}"
            wt = f"[{pos}/{totalFiles}] {fileName}"
        elif self.currentImage:
            currentIndex = self.imageFiles.index(os.path.basename(self.currentImage)) + 1
            totalFiles = len(self.imageFiles)
            filecountlen = len(str(totalFiles))
            pos = str(currentIndex).rjust(filecountlen, "0")
            fileName = os.path.join(self.imageFolder, os.path.basename(self.currentImage)).replace("\\", "/")
            wt = f"[{pos}/{totalFiles}] {fileName}"
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
                                        "Model: ", ",",
                                        "<span style='color: #FF9900; font-size: 14px;'><b>", "</b></span>")
        #Lora部分の強調
        comres = pvsubfunc.insert_between_all(comres,
                                        "&lt;lora:", "&gt;",
                                        "<span style='color: #FFFF00; font-size: 14px;'><b>", "</b></span>")
        #各種強調表示
        for pword in {"ADetailer prompt", "ADetailer checkpoint", "Steps:", "steps:"}:
            comres = pvsubfunc.add_around_all(comres, pword, "<span style='color: #CC4400;'>", "</span>")

        return comres

    #T.B.D きちんと要素判定しないと、文字列の検索だけでは厳しい
    def addTextColorComfyUI(self, comstr):
        comres = comstr
        comres = comres.replace('\\"', '\"')
        comres = comres.replace('\\n', '\n')
        comres = pvsubfunc.normalize_newlines(comres, self.NewLine)

        #ComfyUIっぽいファイルはもうまるごとPrompt扱いに
        self.infoPrompt = comres

        #========================================================
        #「Highlighted keywords for ComfyUI」
        #場当たり的だが、少しでも見やすくなりそうな強調表示を追加
        #各自見やすくなるように追加してください
        #========================================================
        promptlists = [
            [" {\"inputs\": {\"text\": \"", "\","],
            ["\"result\": \"", "\"},"],
            ["\"wildcard_text\": \"", "\""],
            ["\"string\": \"", "\""]
        ]
        seedlists = [
            ["{\"seed\": ", ","],
            ["\"noise_seed\": ", "}"]
        ]
        modellists = [
            ["\"unet_name\": \"", "\""],
            ["\"model_name\": \"", "\""],
            ["\"ckpt_name\": \"", "\""],
            ["\"model\": \"", "\""]
        ]
        loralists = [
            ["\"lora_name\": \"", "\""],
        ]
        pwords = [
            "Steps:", "steps:", "\"steps\"",
            "seed:", "\"noise_seed\"", "\"seed\"",
            "\"ckpt_name\"", "\"model_name\"",
            "\"positive_prompt\"", "\"negative_prompt\""
            ]

        #promptを灰色に
        for searchstr in promptlists:
            comres = pvsubfunc.insert_between_all(comres,searchstr[0], searchstr[1],
                    "<span style='color: #CCCCCC;'>", "</span>")
        #SEED番号の強調
        for searchstr in seedlists:
            comres = pvsubfunc.insert_between_all(comres,searchstr[0], searchstr[1],
                    "<span style='color: #00FFFF; font-size: 14px;'><b>", "</b></span>")
        #Model名の強調
        for searchstr in modellists:
            comres = pvsubfunc.insert_between_all(comres,searchstr[0], searchstr[1],
                    "<span style='color: #FF9900; font-size: 14px;'><b>", "</b></span>")
        #Lora部分の強調
        for searchstr in loralists:
            comres = pvsubfunc.insert_between_all(comres,searchstr[0], searchstr[1],
                    "<span style='color: #FFFF00; font-size: 14px;'><b>", "</b></span>")
        #各種強調表示（暫定：webpアニメーションでヒットしそうな項目も追加）
        for pword in pwords:
            comres = pvsubfunc.add_around_all(comres, pword, "<span style='color: #CC4400;'>", "</span>")
        return comres

    def loadImageToQPixmapFromFile(self, file):
        fn, ext = os.path.splitext(file)
        try:
            if ext.lower() in (".jpg", ".webp", ".png"):
                pixmap = QPixmap(file)
            elif ext.lower() in (".avif"):
                img = Image.open(file)
                img = img.convert("RGBA")  # Ensure the image is in RGBA format
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)

                # Display the image in QLabel
                pixmap = QPixmap.fromImage(qimage)
                pass
            else:
                print(f"not support image file type : {ext}")
                return None
        except Exception as e:
            self.imageLabel.setText(f"Failed to load image: {file}. {e}")
            return None
        return pixmap

    def updateInfo(self):
        if not self.currentImage:   return
        if self.zip_data:
            pixmap = self.getPixmapFromZip(self.currentImage)
        else:
            pixmap = self.loadImageToQPixmapFromFile(self.currentImage)
        width, height = pixmap.width(), pixmap.height()
        self.imageWidth, self.imageHeight = width, height
        comment = "- None -"
        imgcomment = ""
        self.filetype = 1   #0:org jpg 1:sd1111 or forge png, 2:comfyUI png, 3:other file
        #ToDo:改行コードの扱いがおかしい
        # pngではreader.textでキャリッジ・リターンが無視されている感じ？
        #imgcomment = sdfileUtility.get_prompt_from_imgfile(self.currentImage)
        if self.zip_data:
            img = self.get_zip_Image(self.currentImage)
        else:
            img = Image.open(self.currentImage)
        imgcomment = sdfileUtility.get_prompt_from_Image(img, self.currentImage)

        if imgcomment and imgcomment != "":
            self.filetype = 1
            if imgcomment.count("inputs") > 3:
                self.filetype = 2
        else:
            self.filetype = 3   #3:other file
            if self.zip_data:
                reader = self.get_zip_QImageReader(self.currentImage)
            else:
                reader = QImageReader(self.currentImage)
            if reader:
                imgcomment = str(reader.text("prompt"))
                if not imgcomment:
                    imgcomment = str(reader.text("Description"))
        if not imgcomment:
            self.filetype = -1
        pvsubfunc.dbgprint(f"filetype = {self.filetype}")

        imagefilename = self.currentImage
        if self.zip_data:
            imagefilename = self.zipstringdecode(self.currentImage)
        # 情報を2種類のフォントで表示
        path_info = f"Path: {imagefilename}"
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

    #zipfileモジュールを利用した場合に文字化けするのでデコードする
    def zipstringdecode(self, name:str):
        #zipfileモジュールだとエンコードの都合で文字化けするのでWindows用に変換
        result = name
        if os.name == 'nt':
            #Windows
            #WindowsであえてUTF-8でzipファイルを作成した場合には逆に文字化けする
            #そんな人はあまりいないはずだが、頻繁にMacとファイルをやり取りする人であればいるかも
            result = name.encode('cp437').decode('cp932')
        elif os.name == 'posix':
            #Mac or Linux
            #エンコードも画面表示もUTF-8のはずなので基本的に何もしなくて良いはず、たぶん
            pass
        else :
            #Unknown OS
            pass
        return result

    def resizeImage(self):
        if self.currentImage:
            if self.zip_data:
                pixmap = self.getPixmapFromZip(self.currentImage)
            else:
                pixmap = self.loadImageToQPixmapFromFile(self.currentImage)
            # 情報表示を考慮した拡大縮小を行う
            imgsize = self.centralWidget.size()
            if self.fullscreen == False:
                correctwidth = self.infoLabelWidth
                if not self.showInfoText:
                    correctwidth = 0
                imgsize.setWidth(imgsize.width() - correctwidth)
            if self.currentImage.lower().endswith(".webp"):
                self.webpmovie.setScaledSize(self.get_fit_size(QImageReader(self.currentImage).size(), imgsize))
            else:
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

        if self.fitscreen != scale:
            #通常モードからFitモードへ
            self.fitscreen = scale
            #現在のウインドウサイズを退避
            self.screenWidth, self.screenHeight = self.width(), self.height()
            lw, lh = self.imageWidth, self.imageHeight  # 画像のサイズ
            # Widghetの領域とウインドウの領域の差分を算出
            correct_height = self.screenHeight - self.centralWidget.height()
            if self.fitscreen == 0:
                lw = lw // 2    # //で割り算を行うことで一般的なintの割り算（切り捨て動作になる）
                lh = lh // 2
            elif self.fitscreen == 2:
                lw = lw * 2
                lh = lh * 2

            if self.showInfoText:
                lw += self.infoLabelWidth   # Prompt情報分の幅を追加
            lh += correct_height        # Widghetの領域とウインドウの領域の差分を追加
            self.resize(lw, lh)
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

    #情報表示のONOFF切替（画面部品のサイズの調整にて実現）
    def toggleInfoText(self):
        gx = self.geometry().x()
        gy = self.geometry().y()
        gw = self.geometry().width()
        gh = self.geometry().height()
        if self.showInfoText:
            self.infoTextEdit.setFixedWidth(0)
            self.setMinimumSize(320, 320)
            self.setGeometry(gx, gy, gw - self.infoLabelWidth, gh)
        else:
            self.infoTextEdit.setFixedWidth(self.infoLabelWidth)
            self.setMinimumSize(320 + self.infoLabelWidth, 320)
            self.setGeometry(gx, gy, gw + self.infoLabelWidth, gh)
        self.showInfoText = not self.showInfoText
        self.show()     #ウィジェットが表示/非表示などを切り替える場合など
        self.resizeImage()  # ウィンドウサイズ変更時に画像をリサイズ

    #次の画像
    def showNextImage(self, step=1):
        if self.currentImage:
            fileslen = 0
            if self.zip_data:
                fileslen = len(self.zip_files)
            else:
                fileslen = len(self.imageFiles)
            if (fileslen <= 1): return

            nextIndex = -1
            if self.zip_data:
                currentIndex = self.zip_index
                nextIndex = (currentIndex + step) % fileslen
                self.loadZipImage(nextIndex)
            elif self.imageFiles:
                currentIndex = self.imageFiles.index(os.path.basename(self.currentImage))
                nextIndex = (currentIndex + step) % fileslen
                self.loadImage(os.path.join(self.imageFolder, self.imageFiles[nextIndex]).replace("\\", "/"))

            if nextIndex < currentIndex:
                self.showStatusBarMes("back to front")
                self.play_wave(self.soundMoveTop)
            else:
                self.showStatusBarMes("")

    #前の画像
    def showPreviousImage(self, step=1):
        if self.currentImage:
            fileslen = 0
            if self.zip_data:
                fileslen = len(self.zip_files)
            else:
                fileslen = len(self.imageFiles)
            if (fileslen <= 1): return

            prevIndex = -1
            if self.zip_data:
                currentIndex = self.zip_index
                prevIndex = (currentIndex - step) % fileslen
                self.loadZipImage(prevIndex)
            elif self.imageFiles:
                currentIndex = self.imageFiles.index(os.path.basename(self.currentImage))
                prevIndex = (currentIndex - step) % fileslen
                self.loadImage(os.path.join(self.imageFolder, self.imageFiles[prevIndex]).replace("\\", "/"))

            if prevIndex > currentIndex:
                self.showStatusBarMes("back to rear")
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
        if self.currentImage:
            srcfile = self.currentImage
            if not self.zip_data and not os.path.isfile(srcfile):
                self.showStatusBarErrorMes(f"not exist file [{srcfile}]")
                return
            if not os.path.isdir(destdir):
                self.showStatusBarErrorMes(f"not exist dir [{destdir}]")
                return

            dest_file = os.path.join(destdir, os.path.basename(srcfile)).replace("\\", "/")

            # コピー先に同名のファイルがすでに存在していれば削除のみ実行
            if os.path.exists(dest_file):
                os.remove(dest_file)
                self.showStatusBarMes(f"copy cansel [{dest_file}]")
                self.play_wave(self.soundFileCansel)
                return

            if self.zip_data:
                self.copyFromZipdata(srcfile, dest_file)
            else:
                shutil.copy2(srcfile, destdir)
            self.showStatusBarMes(f"copyed [{dest_file}]")
            self.play_wave(self.soundFileCopyOK)

    def copyFromZipdata(self, fname, destfullpath):
        # ファイルを抽出して保存
        with self.zip_data.open(fname) as source_file, open(destfullpath, 'wb') as output_file:
            output_file.write(source_file.read())

        # タイムスタンプを取得して適用
        zip_info = self.zip_data.getinfo(fname)
        timestamp = time.mktime(zip_info.date_time + (0, 0, -1))
        os.utime(destfullpath, (timestamp, timestamp))

    #ムーブ処理
    def moveImageFile(self):
        if self.zip_data:
            self.showStatusBarErrorMes(f"not support - move cannot be performed on zip files")
            return

        if self.currentImage:
            srcfile = self.currentImage
            destdir = self.imageFileMoveDir
            dest_file = os.path.join(destdir, os.path.basename(srcfile)).replace("\\", "/")

            if not os.path.isdir(destdir):
                self.showStatusBarErrorMes(f"not exist dir [{destdir}]")
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
        self.zip_fname = ""
        self.zip_files = None
        self.zip_data = None
        if os.path.isfile(fname):
            if fname.lower().endswith(".zip"):
                try:
                    with open(fname, "rb") as f:
                        zip_bytes = io.BytesIO(f.read())
                        self.zip_data = zipfile.ZipFile(zip_bytes, "r")
                    self.zip_files = self.get_zip_filelist()
                    self.zip_index = 0
                    if self.zip_files and len(self.zip_files) > 0:
                        #以降、self.zip_dataがNoneでない＝zip表示中として扱う
                        self.zip_fname = fname
                        self.loadZipImage(self.zip_index)
                    else:
                        self.zip_data = None
                        self.showStatusBarErrorMes(f"no image files in this zipfile")
                except Exception as e:
                    self.zip_data = None
                    self.showStatusBarErrorMes(f"error : zipfile load")
            else:
                self.loadImage(fname)
        elif os.path.isdir(fname):
            files = sorted([f for f in os.listdir(fname) if f.lower().endswith(SUPPORT_EXT)])
            if len(files) > 0:
                self.loadImage(os.path.join(fname, files[0]).replace("\\", "/"))
            else:
                self.showStatusBarErrorMes(f"no image files in this folder")
        else:
            self.showStatusBarErrorMes(f"not support file type")

    def get_zip_filelist(self):
        return [f for f in self.zip_data.namelist() if f.lower().endswith(SUPPORT_EXT)]

    def get_zip_Image(self, fname):
        img = None
        with self.zip_data.open(fname) as file:
            imgdata = file.read()
            img = Image.open(io.BytesIO(imgdata))
        return img

    def get_zip_QImageReader(self, fname):
        reader = None
        try:
            with self.zip_data.open(fname) as file:
                imgdata = file.read()
                byte_array = QByteArray(imgdata)
                reader = QImageReader()
                reader.setDecideFormatFromContent(True)
                reader.setDevice(io.BytesIO(byte_array))
        except Exception as e:
            #QImageReader.setDevice()が巨大なファイル(数万dotの画像)だと例外が起きる
            #目的がファイルコメントの取得なのでエラー扱いにせず、プリントのみとしておく
            print(f"worning : zipfile QImageReader")
            return None
        return reader

    #========================================
    #= キーイベント処理（QTextBoxにて消費される分）
    #= https://doc.qt.io/qt-5/qt.html#Key-enum
    #========================================
    # 【重要】カーソルキーなどはkeyPressEventに通知されません。ここに記載してください
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # カーソルキーの判定
            keyid = event.key()
            if keyid in {Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Enter, Qt.Key_Return, Qt.Key_PageUp, Qt.Key_PageDown}:
                if keyid == Qt.Key_Right:
                    self.showNextImage()        #次のイメージへ
                elif keyid == Qt.Key_Left:
                    self.showPreviousImage()    #前のイメージへ
                if keyid == Qt.Key_PageDown:
                    self.showNextImage(10)      #10ファイル先のイメージへ
                elif keyid == Qt.Key_PageUp:
                    self.showPreviousImage(10)  #10ファイル前のイメージへ
                elif keyid in {Qt.Key_Enter, Qt.Key_Return}:
                    self.toggleFullscreen()     #全画面切り替え
                elif keyid == Qt.Key_Up:
                    self.copyImageFile(self.imageFileCopyDir)        #コピー処理
                elif keyid == Qt.Key_Down:
                    self.moveImageFile()        #ムーブ処理
                    #self.copyImageFile(self.imageFileMoveDir)        #コピー処理２（設定のムーブフォルダへコピー）
                    #self.showMinimized()        #ウィンドウを最小化
                return True  # イベントをここで処理したとみなして消費
        return super().eventFilter(obj, event)

    #========================================
    #= キーイベント処理（通常）
    #= https://doc.qt.io/qt-5/qt.html#Key-enum
    #========================================
    def keyPressEvent(self, event):
        keyid = event.key()
        pvsubfunc.dbgprint(f"[DBG] keyid : {keyid}")
        #Ctrlキー併用は別で処理する
        if event.modifiers() & Qt.ControlModifier:
            if keyid in {Qt.Key_W}:
                self.appexit()
        #1/2倍表示
        elif keyid == Qt.Key_0:
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
        #10ファイル先のイメージへ
        elif keyid in {Qt.Key_C}:       #Qt.Key_PageDownはeventFilter()にて記載
            self.showNextImage(10)      #10ファイル先のイメージへ
        #10ファイル前のイメージへ
        elif keyid in {Qt.Key_Z}:       #Qt.Key_PageUpはeventFilter()にて記載
            self.showPreviousImage(10)  #10ファイル前のイメージへ
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
        #Prompt情報表示のオンオフ
        elif keyid in {Qt.Key_I}:
            self.toggleInfoText()
        #終了処理
        elif keyid in {Qt.Key_Escape, Qt.Key_Q, Qt.Key_Slash, Qt.Key_Backslash}:
            self.appexit()
        super().keyPressEvent(event)

    def appexit(self):
        #キーによる終了でなかった場合に、ここの処理が行われないためcloseEventに移動
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
            if os.path.isfile(filePath):
                if not filePath.lower().endswith(".zip") and not any(filePath.lower().endswith(ext) for ext in SUPPORT_EXT):
                    return
            self.loadFile(filePath)

    # マウスボタンプレスイベント（押し始め）
    def mousePressEvent(self, event):
        pvsubfunc.dbgprint(f"[DBG] mouse button : {event.button()}")
        if event.button() == Qt.LeftButton and not self.fullscreen:
            self.dragging = True
            self.last_pos = event.globalPos()
        elif event.button() == Qt.RightButton:
            self.copyImageFile(self.imageFileCopyDir)        #コピー処理

    # マウス移動イベント
    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.globalPos() - self.last_pos
            self.move(self.pos() + delta)
            self.last_pos = event.globalPos()

    # マウスボタンリリースイベント（離した時）
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    # webpを再生中なら停止する
    def stop_WEbpMovie(self):
        if self.webpmovie != None:
            self.webpmovie.stop()
            self.webpmovie = None

    # 元のサイズをターゲットサイズにフィットさせた場合のサイズを取得
    def get_fit_size(self, size_org, size_target):
        scaled_width = size_target.width()
        scaled_height = int(size_org.height() * (scaled_width / size_org.width()))
        if scaled_height > size_target.height():
            scaled_height = size_target.height()
            scaled_width = int(size_org.width() * (scaled_height / size_org.height()))
        return QSize(scaled_width,scaled_height)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())
