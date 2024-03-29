from flask import Flask, render_template
import glob
import os
import piexif
from PIL import Image
from PIL.ExifTags import TAGS
import imghdr

MAXSIZE = 1000
EXIFPARAMS = "Artist", "Make", "Model", "Software", "DateTimeOriginal", "ShutterSpeedValue", "ApertureValue", "BrightnessValue", "FocalLength", "ExifImageWidth", "ExifImageHeight", "FocalPlaneXResolution", "FocalPlaneYResolution", "ExposureTime", "FNumber", "ISOSpeedRatings", "LensMake", "LensModel", "ImageWidth", "ImageLength", "FocalLengthIn35mmFilm"




app = Flask(__name__)

@app.route("/")
def home():
    #image resize max width
    maxsize = MAXSIZE
    cdpath = os.path.dirname(os.path.realpath(__file__))
    images = [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]
    thumbs = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]
    imagesdir = cdpath + "/static/images/"
    thumbsdir = cdpath + "/static/thumbs/"

    def resize_image(input_path, output_path, max_size):
        image = Image.open(input_path)
        width, height = image.size
        aspect_ratio = width / height
        new_width = max_size
        new_height = int(new_width / aspect_ratio)
        resized_image = image.resize((new_width, new_height))
        resized_image.save(output_path, optimize=True, quality=80)


        
        #removes gps data from jpeg images
        for i in images:
            if imghdr.what(cdpath+'/static/images/'+i) != "jpeg":
                pass
            else:
                img = piexif.load(cdpath+'/static/images/'+i)
                if 'GPS' in img:
                    del img['GPS']
                    exif_bytes = piexif.dump(img)
                    piexif.insert(exif_bytes, cdpath+'/static/images/'+i)

    #checks for new images, and makes thumbnails
    if set(images) != set(thumbs):
        uniques = set(images) - set(thumbs)
        for i in uniques:
            imgdir = imagesdir + i
            savedir = thumbsdir + i
            resize_image(imgdir, savedir, maxsize)

    thumbslater = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]
    return render_template("index.html", imges=thumbslater)


@app.route("/<image>")
def image(image):
    cdpath = os.path.dirname(os.path.realpath(__file__))
    image_path = cdpath + "/static/images/" + image
    def get_image_exif(image_path):
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        if exif_data is None:
            return []
        exif_list = []
        
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if  len(str(value)) <= 150:
                exif_list.append((tag_name, value))
        
        return exif_list
    try:
        exif_data = get_image_exif(image_path)
        #exif data filtering
        exif_data_list = [(tag_name, value) for tag_name, value in exif_data if tag_name in (EXIFPARAMS)]
    except:
        exif_data_list = ""
    return render_template("image.html", link=image, metadata=exif_data_list)

if __name__ == '__main__':
    app.run(debug=True)
