from flask import Flask, render_template
import glob
import os
import piexif
from PIL import Image
from PIL import ImageFile
from PIL.ExifTags import TAGS
import exifread

ImageFile.LOAD_TRUNCATED_IMAGES = True

MAXSIZE = 1000
EXIFPARAMS = "Make", "Model", "Software", "DateTimeOriginal", "ShutterSpeedValue", "ApertureValue", "BrightnessValue", "FocalLength", "ExifImageWidth", "ExifImageHeight", "ExposureTime", "FNumber", "ISOSpeedRatings", "LensMake", "LensModel", "ImageWidth", "ImageLength","Artist", "FocalLengthIn35mmFilm"



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

    #remove gps data
    for i in images:
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
    high = []
    wide = []
    for i in thumbslater:
        image = Image.open(cdpath + "/static/thumbs/" + i)
        width, height = image.size
        if width > height:
            wide.append(i)
        else:
            high.append(i)

    

    return render_template("index.html", wide=wide, high=high)


@app.route("/<image>")
def image(image):
    cdpath = os.path.dirname(os.path.realpath(__file__))
    image_path = cdpath + "/static/images/" + image
    
    def extract_film_simulation(image_path):
        # Open the image file in binary mode
        with open(image_path, 'rb') as f:
            # Read the EXIF data
            tags = exifread.process_file(f)

        # Define the Fujifilm Film Simulation tag
        fujifilm_film_simulation_tag = 'MakerNote Tag 0x1401'

        # Check if the Fujifilm Film Simulation tag exists
        if fujifilm_film_simulation_tag in tags:
            # Get the Film Simulation value
            film_simulation_value = tags[fujifilm_film_simulation_tag].values
            return film_simulation_value
        return None

    def get_output(value):
        value_mapping = {
            0: "Provia (standard)",
            256: "Studio Portrait",
            272: "Studio Portrait Enhanced Saturation",
            288: "Astia",
            304: "Studio Portrait Increased Sharpness",
            512: "Velvia (Fujichrome)",
            768: "Studio Portrait Ex",
            1024: "Velvia",
            1280: "Pro Neg. Std",
            1281: "Pro Neg. Hi",
            1536: "Classic Chrome",
            1792: "Eterna",
            2048: "Classic Negative",
            2304: "Bleach Bypass",
            2560: "Nostalgic Neg",

        }
        if value in value_mapping:
            return value_mapping[value]
        else:
            return ""

    def get_image_exif(image_path):
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        if exif_data is None:
            return []
        exif_list = []
        
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            
            exif_list.append((tag_name, value))
        
        return exif_list
    try:
        exif_data = get_image_exif(image_path)

        film_simulation = extract_film_simulation(image_path)
        if film_simulation is None:
            film_simulation = ""
        exif_data_list = [(tag_name, value) for tag_name, value in exif_data if tag_name in (EXIFPARAMS)]
    except:
        exif_data_list = ""
        film_simulation = ""
    if film_simulation == "":
        film_value = ""
    else:
        film_value = get_output(film_simulation[0])
    

    return render_template("image.html", link=image, metadata=exif_data_list, film_sim=film_value)

if __name__ == '__main__':
    app.run()
