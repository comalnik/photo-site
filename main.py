from flask import Flask, render_template
import glob
import os
import piexif
app = Flask(__name__)


#Todo---Make images redirect to custom route in flask. The route has a html template that displays full size image and possibly metadata.

@app.route("/")
def home():
    cdpath = os.path.dirname(os.path.realpath(__file__))
    names = [os.path.basename(x) for x in glob.glob(cdpath+"/static/images/*")]
    
    for i in names:
        img = piexif.load(cdpath+'/static/images/'+i)
        if 'GPS' in img:
            del img['GPS']
            exif_bytes = piexif.dump(img)
            piexif.insert(exif_bytes, cdpath+'/static/images/'+i)

    
    return render_template("index.html", imges=names)


if __name__ == '__main__':
    app.run()