from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import glob
import os
import piexif
from PIL import Image
from PIL import ImageFile
from PIL.ExifTags import TAGS
import exifread
from werkzeug.security import generate_password_hash, check_password_hash

ImageFile.LOAD_TRUNCATED_IMAGES = True

MAXSIZE = 1000
EXIFPARAMS = "Make", "Model", "Software", "DateTimeOriginal", "ShutterSpeedValue", "ApertureValue", "BrightnessValue", "FocalLength", "ExifImageWidth", "ExifImageHeight", "ExposureTime", "FNumber", "ISOSpeedRatings", "LensMake", "LensModel", "ImageWidth", "ImageLength","Artist", "FocalLengthIn35mmFilm"
UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/static/images/'

#admin password hash, default=admin
ADMIN_PASSWORD = 'scrypt:32768:8:1$nBPz5NHgkknIazWl$e33b8faf3edbc1386955b502150b3013fc1051674066d5149e2ab1fdbd484918dfc61321e668ab7534d12dc1a37c472001b0c154c846c2e7cda108cd472697a3'




app = Flask(__name__)
app.secret_key = 'your_secret_key'


#########functions##################
def resize_image(input_path, output_path, max_size):
    image = Image.open(input_path)
    width, height = image.size
    aspect_ratio = width / height
    new_width = max_size
    new_height = int(new_width / aspect_ratio)
    resized_image = image.resize((new_width, new_height))
    resized_image.save(output_path, optimize=True, quality=80)




@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Check the login credentials
        if check_password_hash(ADMIN_PASSWORD, request.form['password']) == True:
            # Save the login status in the session
            session['logged_in'] = True
            return redirect(url_for('admin'))


    #image resize max width
    maxsize = MAXSIZE
    cdpath = os.path.dirname(os.path.realpath(__file__))
    images = [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]
    thumbs = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]
    imagesdir = cdpath + "/static/images/"
    thumbsdir = cdpath + "/static/thumbs/"


    #remove gps data
    for i in images:
        try:
            img = piexif.load(cdpath+'/static/images/'+i)
            if 'GPS' in img:
                del img['GPS']
                exif_bytes = piexif.dump(img)
                piexif.insert(exif_bytes, cdpath+'/static/images/'+i)
        except:
            pass

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


@app.route("/admin", methods=['GET', 'POST'])
def admin():

    if 'logged_in' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':

        #get id of image to remove
        button_id = request.form.get('button_id')

        #image resize max width
        maxsize = MAXSIZE
        cdpath = os.path.dirname(os.path.realpath(__file__))
        images = [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]
        thumbs = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]
        imagesdir = cdpath + "/static/images/"
        thumbsdir = cdpath + "/static/thumbs/"

        #remove image, thumbs
        if button_id == 'ADDIMG':
            print(button_id)

        else:
            os.remove(imagesdir + button_id)
            os.remove(thumbsdir + button_id)


        #remove gps data
        for i in images:
            try:
                img = piexif.load(cdpath+'/static/images/'+i)
                if 'GPS' in img:
                    del img['GPS']
                    exif_bytes = piexif.dump(img)
                    piexif.insert(exif_bytes, cdpath+'/static/images/'+i)
            except:
                pass

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

        

        return render_template("admin.html", wide=wide, high=high)
    else: 
        #image resize max width
        maxsize = MAXSIZE
        cdpath = os.path.dirname(os.path.realpath(__file__))
        images = [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]
        thumbs = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]
        imagesdir = cdpath + "/static/images/"
        thumbsdir = cdpath + "/static/thumbs/"


        #remove gps data
        for i in images:
            try:
                img = piexif.load(cdpath+'/static/images/'+i)
                if 'GPS' in img:
                    del img['GPS']
                    exif_bytes = piexif.dump(img)
                    piexif.insert(exif_bytes, cdpath+'/static/images/'+i)
            except:
                pass

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

        

        return render_template("admin.html", wide=wide, high=high)





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
            
            exif_list.append((tag_name, value))
        
        return exif_list
    try:
        exif_data = get_image_exif(image_path)
        exif_data_list = [(tag_name, value) for tag_name, value in exif_data if tag_name in (EXIFPARAMS)]
    except:
        exif_data_list = ""

    

    return render_template("image.html", link=image, metadata=exif_data_list)

if __name__ == '__main__':
    app.run()
