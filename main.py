from flask import Flask, render_template
import glob
import os
import piexif
from PIL import Image
app = Flask(__name__)
#Todo---Make images redirect to custom route in flask. The route has a html template that displays full size image and possibly metadata.

@app.route("/")
def home():

    maxsize = 1000
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

    for i in images:
        img = piexif.load(cdpath+'/static/images/'+i)
        if 'GPS' in img:
            del img['GPS']
            exif_bytes = piexif.dump(img)
            piexif.insert(exif_bytes, cdpath+'/static/images/'+i)


    if set(images) != set(thumbs):
        uniques = set(images) - set(thumbs)
        for i in uniques:
            imgdir = imagesdir + i
            savedir = thumbsdir + i
            resize_image(imgdir, savedir, maxsize)

    thumbslater = [os.path.basename(x) for x in glob.glob(cdpath+"/static/thumbs/*")]
    return render_template("index.html", imges=thumbslater)


if __name__ == '__main__':
    app.run(debug=True)