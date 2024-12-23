import json
import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

#デバッグ用のコードの有効無効切り替え 0:無効、1:有効
_IS_DEBUG = 0

#for debug
def dbgprint(message):
    if _IS_DEBUG:
        # date time string
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        # print message
        print(f"[{timestamp}] {message}")

#json形式の設定ファイルから指定されたキーの値を読み込む
def read_value_from_config(config_file, key):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return config_data.get(key, None)

    except FileNotFoundError:
        print(f"エラー: 設定ファイルが見つかりません: {config_file}")
        return None
    except json.JSONDecodeError:
        print(f"エラー: 設定ファイルが正しいjson形式ではありません: {config_file}")
        return None

#json形式の設定ファイルへ指定されたキーの値を書き込む
def write_value_to_config(config_file, key, value):
    try:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config_data = {}
        config_data[key] = value
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True

    except Exception as e:
        print(f"エラー: 設定ファイルへの書き込み中に問題が発生しました: {e}")
        return False

#文字列内のダブルバックスラッシュ (\\) をシングルバックスラッシュ (\) に置換
def replace_double_backslash(input_string):
    return input_string.replace("\\\\", "\\")

#テキスト内のすべての改行コード (\r\n, \r, \n) を指定された改行文字に統一
def normalize_newlines(text, newline="\n"):
    # まず \r\n を \n に置換し、その後 \r を \n に置換
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_text = normalized_text.replace("\n", newline)
    # 必要に応じて統一改行文字に置き換える
    return normalized_text

"""
# 使用例
input_text = "Hello\r\nWorld!\rThis is a test.\nNewline normalization."
result = normalize_newlines(input_text)
"""

#指定文字AとBの前後にCとDを追加する（特定文字を見つけて前後にHTMLタグなどを追加）
def insert_between_all(text, char_a, char_b, insert_c, insert_d):
    start_index = 0
    while True:
        # Aの位置を検索
        start_index = text.find(char_a, start_index)
        if start_index == -1:
            break  # Aが見つからない場合、処理終了

        start_index += len(char_a)  # Aの直後の位置
        end_index = text.find(char_b, start_index)
        if end_index == -1:
            break  # Bが見つからない場合、処理終了

        # AとBの間を抽出し、CとDを追加
        middle_content = text[start_index:end_index]
        modified_middle_content = f"{insert_c}{middle_content}{insert_d}"
        # 元の文字列を更新
        text = text[:start_index] + modified_middle_content + text[end_index:]
        # 次の検索の開始位置を設定
        start_index = end_index + len(char_b)
    return text
"""
# 使用例
original_text = "hoge,<lora:LowRa:0>ほげ,<lora:Another:1>追加"
char_a = "<lora:"
char_b = ">"
insert_c = "abc"
insert_d = "xyz"

result = insert_between_all(original_text, char_a, char_b, insert_c, insert_d)
print(result)

#結果
hoge,<lora:abcLowRa:0xyz>ほげ,<lora:abcAnother:1xyz>追加
"""

#指定文字Aの前後に特定文字列CとDを追加する関数。
def add_around_all(text, target, prefix, suffix):
    result = ""
    start_index = 0

    while True:
        # Aの位置を検索
        index = text.find(target, start_index)
        if index == -1:
            # 残りの文字列を追加して終了
            result += text[start_index:]
            break

        # ターゲットの前までの文字列を追加
        result += text[start_index:index]

        # ターゲットの前後にCとDを追加
        result += prefix + target + suffix

        # 次の検索の開始位置を更新
        start_index = index + len(target)

    return result

"""
# 使用例
original_text = "abcdefghijklmnopqrstu"
target = "ghi"
prefix = "012"
suffix = "345"

result = add_around(original_text, target, prefix, suffix)
print(result)

#結果
abcdef012ghi345jklmnopqrstu
"""

#指定文字AとBに囲まれた部分を取得する
def extract_between(text, char_a, char_b):
    results = []
    start_index = 0

    while True:
        # Aの位置を検索
        start_index = text.find(char_a, start_index)
        if start_index == -1:
            break  # Aが見つからない場合、処理終了

        start_index += len(char_a)  # Aの直後の位置
        end_index = text.find(char_b, start_index)
        if end_index == -1:
            break  # Bが見つからない場合、処理終了

        # AとBの間の部分をリストに追加
        results.append(text[start_index:end_index])

        # 次の検索の開始位置を更新
        start_index = end_index + len(char_b)

    return results

"""
# 使用例
original_text = "Here is <tag>content1</tag> and <tag>content2</tag>."
char_a = "<tag>"
char_b = "</tag>"
result = extract_between(original_text, char_a, char_b)
print(result)

#結果
['content1', 'content2']
"""

#JPG画像ファイルからコメントを取得
def get_jpg_comment(file_path):
    try:
        # 画像を開く
        img = Image.open(file_path)
        # Exifデータを取得
        exif_data = img._getexif()

        if exif_data is None:
            return None

        # タグ名でアクセス可能な形式に変換
        exif = {TAGS.get(tag): value for tag, value in exif_data.items() if tag in TAGS}

        # コメントに関連するタグをチェック
        user_comment = exif.get("UserComment")
        if not user_comment:
            user_comment = exif.get("ImageDescription")
        if user_comment.startswith(b'UNICODE\x00'):
            user_comment = user_comment[len(b'UNICODE\x00'):]
        user_comment = user_comment.replace(b'\x00', b'')
        user_comment = user_comment.decode('utf-8')
        return user_comment
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

#自作の変換ツールを通したjpgをImageライブラリで読み込むと不要なバイトなどがあるので修正する
def remove_jpg_comment_Exifbyte(str):
    resstr = str
    resstr = resstr.replace("b'","")        #ファイルの先頭コード
    resstr = resstr.replace("\\x00'","")    #ファイルの終端コード
    resstr = resstr.replace("\\\\", "\\")   #jpg変換時の問題？
    return resstr
