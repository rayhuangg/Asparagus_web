# django_asparagus
Asparagus monitoring system implemented using django

http://digiag.bime.ntu.edu.tw:3000/

![](https://github.com/JustinBear99/django_asparagus/blob/master/homepage.jpg)

## Home
Home page of the system.

## Record
Display the stored image data of each section and perform model detection.
* Front view of the field robot vehicle
* Demo range selection
* 2d array of buttons representing the sections in the field

## Monitor
Demonstrate detailed model detection results
1. User selects the interested detection result and the specific section from the left hand side
2. Then the detection result will be overlayed on the original image with SVG polygon and rect.
   Each SVG element is clickable and the detailed detection results will show on the right hand side
3. If the clicked target is "spear", and scale is detected, the growth model for spear length prediction will be activated in the Toast.

## Stats
Statistical analysis for the detection results.
1. User select the range of demos from the first two Selects.
2. After the calculation finished, user can then select the categry from the third select.
3. Also, if the spear is selected, the length prediction feature will also be available.

## Lidar
Show the Lidar scanning in real-time. Robot vehicle is required.

## Admin
Admin page for accessing the database.


<details>
<summary>Folder/ File explain</summary>

```
api                    // 提供佐翼查詢section最新辨識結果功能
asparagus              // 主要設定目錄，內有setting.py，原本專案應是較做asparagus，而非目前django_asparagus
css                    //
detectron              // detectron2運行model使用
home                   //
lidar                  //
monitor                //
record                 //
static                 //
stats                  //
templates              //
db.sqlite3             //
manage.py              //
routine.py             // 每天定時執行demo predict
```
</details>