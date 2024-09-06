import requests

def upload_side(side, section, imagepath, filename="foo", detection=False):
    url = "http://digiag.bime.ntu.edu.tw:3000/record/side/"
    image = open(imagepath, "rb")

    data = {"section": section}
    if filename != "foo":
        data["name"] = filename
    if detection:
        data["detection"] = True
    if side:
        data["side"] = side

    r = requests.post(url, data=data, files={"image": image})

    if r.status_code == 200:
        print("Successully uploaded!")
    else:
        print(f"Error uploading... status code: {r.status_code}")

    image.close()

section = "C20"
imagepath = "20231027_09_57_09.jpg"
filename = "20231027_09_57_09.jpg"
side = "left" # "left" or "right" or None
detection = False

upload_side(side=side, section=section, imagepath=imagepath, filename=filename, detection=detection)
