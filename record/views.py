from django.shortcuts import render, reverse, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.timezone import get_current_timezone
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

# Create your views here.

@csrf_exempt
def index(request):

    context = {}
    levels = {}
    now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei'))

    sections = Section.objects.all()
    for section in sections:
        try:
            latest_img = ImageList.objects.filter(section__name=section.name).latest()
            timedelta = now - latest_img.date.astimezone(pytz.timezone('Asia/Taipei'))
            if timedelta.total_seconds() >= 360:
                level = 'warning'
                if timedelta.total_seconds() >= 3600*24:
                    level = 'danger'
            else:
                level = 'primary'
        except:
            level = 'danger'
        context[section.name] = {'section': section.name, 'imagelist':ImageList.objects.filter(section__name=section.name)[:3]}
        levels[section.name] = level
    frontview = FrontView.objects.get(id=399)
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
        if request.POST['section'][0] == 'A' or request.POST['section'][0] == 'D':
            side = 'right'
        else:
            side = 'left'
        # form.save()
        if form.is_valid():

            section = Section.objects.get(name=request.POST['section'])
            image = request.FILES['image']
            try:
                name = request.POST['name']
            except:
                name = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y%m%d_%H%M%S')
            ImageList(section=section, name=name, image=image).save()

            image = ImageList.objects.latest().image.path


            # upload to Joe's lab
            # uploadtosql(request.POST['section'], image, side)

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
        # form.save()
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
    else:
        form = FrontViewForm()

    return render(request, 'record/record.html', {'form': form})

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
