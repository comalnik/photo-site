import os
import glob
import piexif
from flask import Flask, render_template, request, redirect, url_for, session, flash
from PIL import Image
from PIL import ImageFile
from PIL.ExifTags import TAGS
import exifread
from werkzeug.security import check_password_hash

MAXSIZE = 1000
#admin password hash
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
EXIFPARAMS = "Make", "Model", "Software", "DateTimeOriginal", "ShutterSpeedValue", "ApertureValue", "BrightnessValue", "FocalLength", "ExifImageWidth", "ExifImageHeight", "ExposureTime", "FNumber", "ISOSpeedRatings", "LensMake", "LensModel", "ImageWidth", "ImageLength","Artist", "FocalLengthIn35mmFilm"
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Ensure paths end with a separator or handle joins correctly
cdpath = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(cdpath, 'static', 'images')
THUMB_FOLDER = os.path.join(cdpath, 'static', 'thumbs')

if not ADMIN_PASSWORD_HASH:
    raise RuntimeError("ADMIN_PASSWORD_HASH environment variable not set")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "zVEIXdNUqmixcifpxg0IX00pZikYZLTi")


#########functions##################
def resize_image(input_path, output_path, max_size):
    try:
        img = Image.open(input_path)
        
        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        width, height = img.size
        aspect_ratio = width / height
        new_width = max_size
        new_height = int(new_width / aspect_ratio)
        
        resized_img = img.resize((new_width, new_height))
        resized_img.save(output_path, optimize=True, quality=80)
    except Exception as e:
        print(f"Error creating thumbnail for {input_path}: {e}")


def remove_gps_from_single_file(filepath):
    try:
        img = piexif.load(filepath)
        if 'GPS' in img:
            del img['GPS']
            exif_bytes = piexif.dump(img)
            piexif.insert(exif_bytes, filepath)
            return True
    except:
        pass
    return False

def make_thumbnail_batch(images_list, thumbs_list):
    created_count = 0
    # Create missing thumbs
    if set(images_list) != set(thumbs_list):
        uniques = set(images_list) - set(thumbs_list)
        for i in uniques:
            imgdir = os.path.join(UPLOAD_FOLDER, i)
            savedir = os.path.join(THUMB_FOLDER, i)
            resize_image(imgdir, savedir, MAXSIZE)
            created_count += 1
            
    # Remove orphaned thumbs (thumbs with no source image)
    orphans = set(thumbs_list) - set(images_list)
    for i in orphans:
        try:
            os.remove(os.path.join(THUMB_FOLDER, i))
        except:
            pass
            
    return created_count

def aspect_ratio_sort():
    thumbslater = [os.path.basename(x) for x in glob.glob(os.path.join(THUMB_FOLDER, "*"))]
    high = []
    wide = []
    for i in thumbslater:
        try:
            img = Image.open(os.path.join(THUMB_FOLDER, i))
            width, height = img.size
            if width > height:
                wide.append(i)
            else:
                high.append(i)
        except:
            pass 
    return high, wide


def get_image_exif(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
            
        if exif_data is None:
            return []
        exif_list = []
            
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            exif_list.append((tag_name, value))
            
        return exif_list
    except:
        return []


def extract_film_simulation(image_path):
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)

        fujifilm_film_simulation_tag = 'MakerNote Tag 0x1401'
        if fujifilm_film_simulation_tag in tags:
            film_simulation_value = tags[fujifilm_film_simulation_tag].values
            return film_simulation_value
    except:
        pass
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

#home
@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Check the login credentials
        if check_password_hash(ADMIN_PASSWORD_HASH, request.form['password']) == True:
            # Save the login status in the session
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Incorrect Password")

    high, wide = aspect_ratio_sort()
    footer = os.getenv("FOOTER")

    return render_template("index.html", wide=wide, high=high, footer=footer)


#admin page
@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('home'))
        
    images_list = [os.path.basename(x) for x in glob.glob(os.path.join(UPLOAD_FOLDER, "*"))]
    thumbs_list = [os.path.basename(x) for x in glob.glob(os.path.join(THUMB_FOLDER, "*"))]

    if request.method == 'POST':
        
        # 1. DELETE IMAGE
        if 'button_id' in request.form:
            button_id = request.form.get('button_id')
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, button_id))
                os.remove(os.path.join(THUMB_FOLDER, button_id))
                
            except Exception as e:
                pass


        # 2. BATCH GENERATE THUMBNAILS
        elif 'action_thumbs' in request.form:
            count = make_thumbnail_batch(images_list, thumbs_list)
            
        images_list = [os.path.basename(x) for x in glob.glob(os.path.join(UPLOAD_FOLDER, "*"))]
        thumbs_list = [os.path.basename(x) for x in glob.glob(os.path.join(THUMB_FOLDER, "*"))]

    high, wide = aspect_ratio_sort()

    return render_template("admin.html", wide=wide, high=high)


#file upload
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist('file')
        for file in files: 
            if file.filename == '':
                continue
            try:
                filename = file.filename
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                thumb_path = os.path.join(THUMB_FOLDER, filename)
                
                # 1. Save Original
                file.save(save_path) 
                
                # 2. Strip GPS immediately
                remove_gps_from_single_file(save_path)
                
                # 3. Create Thumbnail immediately
                resize_image(save_path, thumb_path, MAXSIZE)
                
            except Exception as e:
                pass
        return redirect(url_for('admin'))


#image display function
@app.route("/<image>")
def image(image):
    if image not in [os.path.basename(x) for x in glob.glob(os.path.join(UPLOAD_FOLDER, "*"))]:
        return render_template("404.html")

    image_path = os.path.join(UPLOAD_FOLDER, image)
    
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