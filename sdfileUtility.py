import os
from PIL import Image, PngImagePlugin
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import piexif.helper
import pillow_avif

def get_exifcomment_from_file(file):
    try:
        img = Image.open(file)
        exif_data = img.info.get("exif")
        if exif_data is None:
            return None
        exif_dict = piexif.load(exif_data)
        comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
        if comment.startswith(b'UNICODE\x00'):
            comment = comment[len(b'UNICODE\x00'):]
        comment = comment.replace(b'\x00', b'')
        comment = comment.decode('utf-8')
        return comment
    except Exception as e:
        print(f"Error get_avifcomment_from_file {file}: {e}")
        return None

def get_pngcomment_from_file(file):
    try:
        with Image.open(file) as img:
            if isinstance(img, PngImagePlugin.PngImageFile):
                metadata = img.info.get("parameters", "") #1:sd1111 or forge png
                #--------
                #T.B.C.:変換後のファイルはComfyUIで開けないが、一応exifコメントには格納しておく用に対応
                #--------
                if not metadata:
                    metadata = img.info.get("prompt", "") #2:comfyUI png
    except Exception as e:
        print(f"Error get_pngcomment_from_file {file}: {e}")
        return None
    return metadata

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
