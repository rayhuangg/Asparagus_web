import requests

def upload_side(side, section, imagepath, filename="foo", detection=False):
    assert side in ["left", "right", "None"]

    url = "http://digiag.bime.ntu.edu.tw:3000/record/side/"

    data = {"section": section}
    if filename != "foo":
        data["name"] = filename
    if detection:
        data["detection"] = True
    if side:
        data["side"] = side

    with open(imagepath, "rb") as image:
        r = requests.post(url, data=data, files={"image": image})

        if r.status_code == 200:
            print("Successully uploaded!")
        else:
            print(f"Error uploading... status code: {r.status_code}")


side = "left" # "left" or "right" or "None"
section = "C21"
imagepath = "left.jpg"
filename = "left.jpg"
detection = False

upload_side(side=side, section=section, imagepath=imagepath, filename=filename, detection=detection)
