import os
from PIL import Image, PngImagePlugin
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import piexif.helper
import pillow_avif

def get_exifcomment_from_file(file):
    try:
        img = Image.open(file)
        comment = get_exifcomment_from_Image(img)
    except Exception as e:
        print(f"Error get_exifcomment_from_file {file}: {e}")
        return None
    return comment

def get_pngcomment_from_file(file):
    try:
        img = Image.open(file)
        comment = get_pngcomment_from_Image(img)
    except Exception as e:
        print(f"Error get_pngcomment_from_file {file}: {e}")
        return None
    return comment

def get_prompt_from_imgfile(img_file):
    fn, ext = os.path.splitext(img_file)
    if ext.lower() in (".jpg", ".webp", ".avif"):
        comment = get_exifcomment_from_file(img_file)
    elif ext.lower() in (".png"):
        comment = get_pngcomment_from_file(img_file)
    else:
        print(f"not support image file type : {ext}")
        return None
    return comment

def get_exifcomment_from_Image(img, fname):
    comment = None
    try:
        exif_data = img.info.get("exif")
        if exif_data is None:
            return None
        exif_dict = piexif.load(exif_data)
        comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
        # ComfyUIで作成したwebpアニメーション対応（暫定）
        if not comment or comment == "":
            comment = exif_dict["0th"].get(272)
        # ComfyUIで作成したPNGをjpg変換したファイルへの対応（暫定）
        if (not comment or comment == ""):
            #本来であれば、promptとworkflowを分離したいところではあるが、、
            keyword = '{"prompt": '
            exifstr = str(exif_data)
            pos = exifstr.find(keyword)
            if pos != -1:
                comment = str.encode(exifstr[pos + len(keyword):])
                comment = comment.replace(b"\\\\", b"\\")
        #もしtupleで返却されればbytes型に変換
        if isinstance(comment, tuple):
            comment = bytes(comment)
        if comment:
            if comment.startswith(b'UNICODE'):
                comment = comment[len(b'UNICODE'):]
            comment = comment.replace(b'\x00', b'')
        comment = comment.decode('utf-8')
    except Exception as e:
        print(f"Error get_exifcomment_from_Image {fname}: {e}")
        return None
    return comment

def get_pngcomment_from_Image(img, fname):
    comment = None
    try:
        if isinstance(img, PngImagePlugin.PngImageFile):
            comment = img.info.get("parameters", "") #1:sd1111 or forge png
            if not comment:
                #--------
                #T.B.C.
                # 変換後のファイルはComfyUIで開けないが、一応exifコメントには格納
                # promptだけではなくworkflowも表示
                #--------
                comment = img.info.get("prompt", "") #2:comfyUI png
                comment += img.info.get("workflow", "") #2:comfyUI png
    except Exception as e:
        print(f"Error get_pngcomment_from_Image {fname}: {e}")
        return None
    return comment

def get_prompt_from_Image(img, fname):
    fn, ext = os.path.splitext(fname)
    if ext.lower() in (".jpg", ".webp", ".avif"):
        comment = get_exifcomment_from_Image(img, fname)
    elif ext.lower() in (".png"):
        comment = get_pngcomment_from_Image(img, fname)
    else:
        print(f"not support image file type : {ext}")
        return None
    return comment


def convert_to_jpgwebp(infile, outfile, quality, comment):
    with Image.open(infile) as img:
        rgb_img = img.convert("RGB")
        rgb_img.save(outfile, quality=quality) #file format is filename ext
        exif_bytes = piexif.dump({
            "Exif": {
                piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(comment or "", encoding="unicode")
            },
        })
        piexif.insert(exif_bytes, outfile)

def convert_to_png(infile, outfile, quality, comment):
        print("not support convert png")
def convert_to_avif(infile, outfile, quality, comment):
        print("not support convert avif")

def convert_image(infile, outfile, imgtype, quality):
    commnet = get_prompt_from_imgfile(infile)
    if imgtype in (".jpg", ".webp"):
        convert_to_jpgwebp(infile, outfile, quality, commnet)
    if imgtype == ".png": #not support
        convert_to_png(infile, outfile, quality, commnet)
    if imgtype == ".avif": #not support
        convert_to_avif(infile, outfile, quality, commnet)
