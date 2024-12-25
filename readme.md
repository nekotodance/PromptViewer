[README in English](readme-en.md)

## PromptViewerについて 0.1.3
StableDiffusionで作成した画像のプロンプト情報を確認しながら、指定フォルダへの振り分けを「片手」で行うのを目的としたツールです  
マウスもしくはキーボードで動作します  
jpg, png, webpファイルの表示をサポートしています  
![PromptViewer-image](docs/PromptViewer-image001.jpg)

## 特徴
- 画像とプロンプトのチェックを片手操作で完結
- Prompt情報やSeed番号のコピー機能により、画像の再生成を支援  
- 気に入った、修正が必要などの画像振り分け  
- とにかくシンプルで高速（を目指してます）    

## インストール方法（簡易）
[簡易インストール版zipのダウンロード] https://github.com/nekotodance/PromptViewer/releases/download/latest/PromptViewer.zip

- zipファイルを解凍
- 解凍したフォルダ内の「pv-install.ps1」を右クリックして「PowerShellで実行」を選択
- イントールの最後にデスクトップにリンクをコピーするかどうかを聞いてきます  
「"Do you want to copy the shortcut to your desktop? (y or enter/n)」  
必要があれば「y」入力後、もしくはそのまま「enter」キー  
必要なければ「n」入力後「enter」キー  
- PromptViewerリンクが作成されます

リンクファイルをダブルクリック、もしくはリンクファイルにそのまま画像をドラッグ＆ドロップして起動できます

## インストール方法（手動）
インストールフォルダをC:\tool\git\PromptViewerとした場合で説明  
！Pythonはインストールされていて最低限の知識はあるものとします！  

#### 1)C:\tool\git\PromptViewerを作成
#### 2)以下のファイルを格納
  PromptViewer.py  
  PromptViewer_beep.wav  
  PromptViewer_filecansel.wav  
  PromptViewer_filecopyok.wav  
  PromptViewer_filemoveok.wav  
  PromptViewer_moveend.wav  
  PromptViewer_movetop.wav  
  pvsubfunc.py  
  
  PromptViewer_settings.json    ※1

※1:設定ファイルはなければ自動で作成されるのでなくても良い
  
#### 3)コマンドプロンプトを立ち上げて以下を実行する。この手順はインストールの一度のみ
###### 3-1)カレントフォルダの移動移動
    c:
    cd C:\tool\git\PromptViewer
###### 3-2)venv環境を作成、activate
    py -m venv venv
    .\venv\Scripts\activate.bat
###### 3-3)利用するライブラリをインストール
    pip install PyQt5 pyperclip Image
###### 3-4)動作確認
    py PromptViewer.py
    
###### 3-5)設定の変更
！「設定ファイルについて」を参照し、image-fcopy-dir、image-fmove-dirを変更のこと！

#### 4)起動に便利なショートカットの作成
  適当なフォルダで右クリックして「新規作成」->「ショートカット」  
「項目の場所を...」に以下を入力
  C:\tool\git\PromptViewer\Scripts\pythonw.exe C:\tool\git\PromptViewer\PromptViewer.py  
  
  今後は作成したショートカットをダブルクリックでアプリのように使えます  
  またこのショートカットにファイル（もしくは画像を格納したフォルダ）をドラッグ＆ドロップも可能  

## 設定ファイルについて
PromptViewer_settings.jsonに以下の情報を保持しています  
！特にimage-fcopy-dir、image-fmove-dirは【自分の環境に合わせて必ず】書き換えてください！  

image-fcopy-dir   : W,上キーによるファイルのコピー先フォルダ名  
image-fmove-dir   : S,下キーによるファイルのムーブ先フォルダ名（こちらはファイルの移動となるので注意）  

info-label-w      : Prompt表示領域の横幅(デフォルト値:480)  
geometry-x,y      : 最後のウインドウ表示位置  
geometry-w,h      : 最後のウインドウ表示サイズ  

以下は効果音となります（WAVEファイルを好きなものに変更可能です、試してませんが）  
sound-beep        : 処理失敗時のエラーオン  
sound-fcopy-ok    : コピー成功時の音  
sound-fmove-ok    : ムーブ成功時の音  
sound-f-cansel    : コピー、ムーブのキャンセル時の音  
sound-move-top    : 次の画像表示時に、一廻りして最初の画像に戻った時の音  
sound-move-end    : 前の画像表示時に、一廻りして最後の画像に戻った時の音  

## 利用方法
アプリ上に画像ファイル（JPGかPNGファイル）、もしくは画像ファイルが入ったフォルダをドラッグ＆ドロップしてください  
インストールの4)で作成したショートカットにドラッグ＆ドロップでも動作します  
またはPython実行時の引数に画像ファイルか画像が入ったフォルダをしていしてください  

#### キー操作（割当を変えたい人はソースのキーイベント処理を好きに書き換えてください）
AD,左右   : 同じフォルダ内の前後の画像に移動  
Q,ESC     : 終了  
0,1,2     : 画像のサイズの0:1/2、1:等倍、2:2倍にフィット表示（トグル動作）  
F,Enter   : 全画面表示に切り替え（トグル動作）  
W,上      : 設定ファイルのimage-fcopy-dirで指定されたフォルダに表示画像をコピー ※2  
S,下      : 設定ファイルのimage-fmove-dirで指定されたフォルダに表示画像をムーブ ※3  
K         : シード番号をコピーバッファへ ※4  
P         : Prompt文字列をコピーバッファへ ※4  
N         : Negative Prompt文字列をコピーバッファへ ※4  
H         : Hires Prompt文字列をコピーバッファへ ※4  

#### マウス操作
ホイール操作      : 同じフォルダ内の前後の画像に移動  
右クリック        : 設定ファイルのimage-fcopy-dirで指定されたフォルダに表示画像をコピー ※2  
左ダブルクリック  : 全画面表示切り替え（トグル動作）  
左ドラッグ       :  ウインドウを移動  

※2:コピーは再度キーを押すことでキャンセル（コピー先から削除）出来ます  
※3:ムーブは再度キーを押すことで取り消し出来ます（画像から移動していない場合のみ可能）  
※4:ComfyUIの出力ファイルには対応していません  

## 画面表示
![PromptViewer-image](docs/PromptViewer-image002.jpg)

#### Window Title
「[現在表示中の画像番号/同一フォルダ内の画像総数] フルパスのファイル名」  

#### Prompt Info
以下のように文字の色や太さを変えて表示
- 灰色 : Prompt  
- 紫色 : Negative Prompt  
- 緑色 : Hires Prompt  
- 黄色太 : Lora名  
- 水色太 : Seed番号  
- 橙色太 : Model名  
- 橙色 : 文字を着色 ADetailer prompt、Steps:、steps:  

※ComfyUIの出力ファイルには部分的にしか対応していません  

#### Status Bar
動作状況の表示

## 注意事項
- Automatic1111、Forge、reForge、ComfyUIの出力ファイルで表示を確認しています  
（ただしComfyUIはノードにより異なるため表示を保証するものではありません）  
- 現状はpngファイルの場合、Prompt情報の中の改行コードがうまく拾えていません。Imageライブラリの利用方法か、文字コードの指定に問題があるかもしれません  
- ComfyUIのPrompt情報のコピーや色付けには対応していません  

## 変更履歴
- 0.1.3 jpg,pngに続きwebpファイルの表示に対応  
- 0.1.2 ComfyUIで生成したPNGファイルのtext部分の色付けと改行に対応（暫定的）  
- 0.1.1 全画面中に終了した場合に、全画面を解除してから終了（変な画面サイズを保存しないため）  
- 0.1.0 色々修正してますがいったん初版  

以上
