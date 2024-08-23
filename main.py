import os
import glob
import piexif
from flask import Flask, render_template, request, redirect, url_for, session
from PIL import Image
from PIL import ImageFile
from PIL.ExifTags import TAGS
import exifread
from werkzeug.security import check_password_hash



MAXSIZE = 1000
#admin password hash
ADMIN_PASSWORD = 'scrypt:32768:8:1$nBPz5NHgkknIazWl$e33b8faf3edbc1386955b502150b3013fc1051674066d5149e2ab1fdbd484918dfc61321e668ab7534d12dc1a37c472001b0c154c846c2e7cda108cd472697a3'
EXIFPARAMS = "Make", "Model", "Software", "DateTimeOriginal", "ShutterSpeedValue", "ApertureValue", "BrightnessValue", "FocalLength", "ExifImageWidth", "ExifImageHeight", "ExposureTime", "FNumber", "ISOSpeedRatings", "LensMake", "LensModel", "ImageWidth", "ImageLength","Artist", "FocalLengthIn35mmFilm"
MAXSIZE = 1000
ImageFile.LOAD_TRUNCATED_IMAGES = True

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/static/images/'
cdpath = os.path.dirname(os.path.realpath(__file__))




#########functions##################
def resize_image(input_path, output_path, max_size):
    image = Image.open(input_path)
    width, height = image.size
    aspect_ratio = width / height
    new_width = max_size
    new_height = int(new_width / aspect_ratio)
    resized_image = image.resize((new_width, new_height))
    resized_image.save(output_path, optimize=True, quality=80)


def remove_gps_data(images):
    for i in images:
        try:
            img = piexif.load(cdpath+'/static/images/'+i)
            if 'GPS' in img:
                del img['GPS']
                exif_bytes = piexif.dump(img)
                piexif.insert(exif_bytes, cdpath+'/static/images/'+i)
        except:
            pass


def make_thumbnail(images, thumbs):
    if set(images) != set(thumbs):
        uniques = set(images) - set(thumbs)
        for i in uniques:
            imgdir = cdpath + "/static/images/" + i
            savedir = cdpath + "/static/thumbs/" + i
            resize_image(imgdir, savedir, MAXSIZE)


def aspect_ratio_sort():
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
    return high, wide


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


def extract_film_simulation(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

    fujifilm_film_simulation_tag = 'MakerNote Tag 0x1401'
    if fujifilm_film_simulation_tag in tags:
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




#######flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'


#home
@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Check the login credentials
        if check_password_hash(ADMIN_PASSWORD, request.form['password']) == True:
            # Save the login status in the session
            session['logged_in'] = True
            return redirect(url_for('admin'))


    images = [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]
    thumbs = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]

    #remove gps data
    remove_gps_data(images)
    #checks for new images, and makes thumbnails
    make_thumbnail(images, thumbs)
    #sorts images based on aspect ratio
    high, wide = aspect_ratio_sort()

    return render_template("index.html", wide=wide, high=high)


#admin page
@app.route("/admin", methods=['GET', 'POST'])
def admin():

    if 'logged_in' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        #get id of image to remove
        button_id = request.form.get('button_id')
        #remove image, thumbs
        os.remove(cdpath + "/static/images/" + button_id)
        os.remove(cdpath + "/static/thumbs/" + button_id)


    images = [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]
    thumbs = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]

    #remove gps data
    remove_gps_data(images)
    #checks for new images, and makes thumbnails
    make_thumbnail(images, thumbs)
    #sorts images based on aspect ratio
    high, wide = aspect_ratio_sort()

    return render_template("admin.html", wide=wide, high=high)


#file upload
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist('file')
        for file in files: 
            try:
                file.save(UPLOAD_FOLDER + file.filename) 
            except:
                pass
        return redirect(url_for('admin'))


#image display function
@app.route("/<image>")
def image(image):
    if image not in [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]:
        return render_template("404.html")


    image_path = cdpath + "/static/images/" + image    
    #get metadata and fujifilm film simulation
    try:
        exif_data = get_image_exif(image_path)
        exif_data_list = [(tag_name, value) for tag_name, value in exif_data if tag_name in (EXIFPARAMS)]
        film_simulation = extract_film_simulation(image_path)
        if film_simulation is None:
            film_simulation = ""

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
