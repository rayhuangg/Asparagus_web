import threading
from django.shortcuts import render, reverse, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


import queue
import requests
from .models import Section, ImageList, FrontView
from .forms import ImageListForm, FrontViewForm
import sys
import os
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from monitor.models import Demo, ResultList
import datetime
import json
import ftplib
import pytz
import time


# Create a global queue to store the IDs of photos that need detection.
detection_queue = queue.Queue()

# Define a global variable to store thread objects.
detection_thread = None

# Define a lock object to protect thread start and stop operations.
thread_lock = threading.Lock()

# Define an exit flag to control thread termination.
exit_thread = False

# Create a global variable to indicate whether scheduled detection is enabled.
enable_detection = False

@csrf_exempt
def index(request):

    context = {}
    levels = {}
    now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei'))

    sections = Section.objects.all()

    # Adjust the color display in record webpage, based on upload time
    for section in sections:
        try:
            latest_img = ImageList.objects.filter(section__name=section.name).latest()
            timedelta = now - latest_img.date.astimezone(pytz.timezone('Asia/Taipei'))
            if timedelta.total_seconds() >= 360: # 360 means 6 mins
                level = 'warning' # warning = orange (probably)
                if timedelta.total_seconds() >= 3600*24:
                    level = 'danger'
            else:
                level = 'primary'
        except:
            level = 'danger'
        context[section.name] = {'section': section.name, 'imagelist':ImageList.objects.filter(section__name=section.name)[:3]}
        levels[section.name] = level
    frontview = FrontView.objects.latest('date')
    # return render(request, 'record/record.html', {'context': context, 'frontview': frontview, 'levels': json.dumps(levels)})
    return render(request, 'record/record.html', {'frontview': frontview, 'levels': json.dumps(levels)})

# def fetchRecord(request):
#     if request.method == 'POST':
#         section = request.POST['section']
#         images = ImageList.objects.filter(section__name=section.name)[:3]

def refreshFront(request):
    if request.method == 'POST':
        frontview = FrontView.objects.latest()
        return HttpResponse(frontview.image.url)

def demoProgress(request):
    if request.method == 'POST':
        with open('monitor/progress.txt', 'r') as progress:
            content = progress.readlines()
        [now, total] = content[0].split()
        return HttpResponse(json.dumps({'now': int(now), 'total': int(total)}))

def preview(request):
    if request.method == 'POST':
        context = []
        sec = request.POST['section']
        imgs = ImageList.objects.filter(section__name=sec)[:3]
        for img in imgs:
            context.append({'name': img.name, 'date': img.date.astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y.%m.%d %H:%M:%S'), 'id': img.id, 'url': img.image.url})
        return HttpResponse(json.dumps({'context': context}))

@csrf_exempt
def side(request):
    form = ImageListForm()
    if request.method == 'POST':
        form = ImageListForm(request.POST, request.FILES)
        if form.is_valid():
            section = Section.objects.get(name=request.POST['section'])
            image = request.FILES['image']
            try:
                name = request.POST['name']
            except:
                name = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y%m%d_%H%M%S')

            side = request.POST.get('side')

            image = ImageList(section=section, name=name, image=image, side=side)
            image.save()

            latest_id = ImageList.objects.latest().id

            if request.POST.get("detection") == "True":
                print("Receive detection commend, starting the patrol detection task.")
                detection_queue.put(latest_id)
                print("Patrol detection task start.")

        else:
            print(form.errors)
    else:
        form = ImageListForm()

    return render(request, 'record/record.html', {'form': form})


@csrf_exempt
def front(request):
    form = FrontViewForm()
    if request.method == 'POST':
        form = FrontViewForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
    else:
        form = FrontViewForm()

    return render(request, 'record/record.html', {'form': form})


# Upload data to Dr. Joe-Air Jiang's lab server
def uploadtosql(location, image, side):
    # try:
    camera_ID = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')
    ftp = ftplib.FTP()
    FTPIP= "140.112.94.126"
    FTPPORT= 3837
    USERNAME= "asparagus"
    USERPWD= "asparagus303"
    ftp.connect(FTPIP, FTPPORT,timeout=3)
    ftp.login(USERNAME,USERPWD)
    # print("[FTP] Login...")
    # print(ftp.getwelcome())
    bufsize = 1024
    # file_handler = open(("/home/pi/Desktop/connect_right/right/"+ location +".jpg"),'rb')
    file_handler = open(image, 'rb')
    ftp.cwd('/Drive_control/' + side + '/')
    ftp.storbinary('STOR %s' % os.path.basename(camera_ID + location +'.jpg'),file_handler,bufsize)
    ftp.set_debuglevel(0)
    file_handler.close()
    ftp.quit()
    # print("ftp_126 upload OK")
    # except:
    #     print("upload error")

def showdemoRange(request):
    if request.method == 'POST':
        fr, un = request.POST['from'], request.POST['until']
        imageset = ImageList.objects.filter(date__range=[fr ,un])
        data = []
        for image in imageset:
            data.append({'url': image.image.url, 'date': image.date.astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y.%m.%d %H:%M:%S'), 'id': image.id, 'section': image.section.name})
        return HttpResponse(json.dumps({'data': data}))


# View function to control the enabling of scheduled detection.
def toggle_detection(request):
    global enable_detection
    global detection_thread
    global exit_thread

    status = request.POST['status']
    print(f"Received status: {status}")

    if status == "start":
        enable_detection = True
        # Start a thread only if it doesn't exist or has already finished.
        with thread_lock:  # Lock to ensure thread safety when checking and modifying the detection_thread.
            if detection_thread is None or not detection_thread.is_alive():
                exit_thread = False  # Reset the exit flag to allow the thread to run.
                detection_thread = threading.Thread(target=perform_detection)
                detection_thread.start()
        print("Start regular execution of identification")

    elif status == "stop":
        enable_detection = False
        with thread_lock:  # Lock to ensure thread safety when stopping the detection thread.
            # Only stop the thread if it exists and is currently running.
            if detection_thread is not None and detection_thread.is_alive():
                exit_thread = True
                # Do not join (wait for the thread to finish) inside the lock to avoid potential deadlock.
            else:
                print("Thread has already been stopped automatically.")
        # Join (wait for the thread to finish) outside the lock to ensure it can clean up without blocking other operations.
        if detection_thread is not None and detection_thread.is_alive():
            detection_thread.join()
        with thread_lock:
            detection_thread = None  # Clear the thread object to indicate it's no longer running.
        print("Stop regular execution of identification, kill session")

    return HttpResponse('Success')

def perform_detection():
    global enable_detection
    global exit_thread

    print("receive toggle trigger")

    last_queue_empty_time = None  # Keeps track of the last time the queue was empty.

    try:
        while not exit_thread:
            if enable_detection:
                # Process tasks in the detection queue.
                while not detection_queue.empty():
                    image_id = detection_queue.get()
                    print(f"{image_id = }")

                    post_data = {
                        "demo_img_id": image_id,
                        "straw": "false",
                        "source": "patrol",
                    }
                    response = requests.post("http://140.112.183.138:3000/monitor/demo/", data=post_data)
                    if response.status_code == 200:
                        print("Successfully demo!")
                    else:
                        print("Fail demo!")

                if detection_queue.empty():
                    print("*** Queue is empty ***")
                    time_range = 300  # Set to 5 minutes (300 seconds).
                    if last_queue_empty_time is None:
                        last_queue_empty_time = time.time()  # Record the time when the queue first becomes empty.
                    elif time.time() - last_queue_empty_time >= time_range:  # Check if the queue has been empty for the specified duration.
                        print(f"Queue has been empty for {time_range} seconds, terminating thread")
                        exit_thread = True  # Terminate the thread if the queue remains empty for 5 minutes.
                else:
                    last_queue_empty_time = None  # Reset the timer if the queue is no longer empty.

            time.sleep(5)  # Check the queue status every 5 seconds.

    finally:
        print("Thread terminated and cleaned up.")