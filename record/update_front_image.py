import requests

url = "http://digiag.bime.ntu.edu.tw:3000/record/front/"
file_path = "front.jpg"  # replace with the actual path to your file

with open(file_path, "rb") as file:
    response = requests.post(url, files={"image": file})

print(response.status_code)
print(response.text)