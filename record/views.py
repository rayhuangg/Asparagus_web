from django.shortcuts import render, reverse, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from .models import Section, ImageList, FrontView
from .forms import ImageListForm, FrontViewForm
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from monitor.models import Demo, ResultList
import datetime
import json

# Create your views here.

@csrf_exempt
def index(request):

    context = {}
    levels = {}
    now = datetime.datetime.now(datetime.timezone.utc)

    sections = Section.objects.all()
    for section in sections:
        try:
            latest_img = ImageList.objects.filter(section__name=section.name)[0]
            timedelta = now - latest_img.date
            if timedelta.days >= 2:
                level = 'warning'
                if timedelta.days >= 4:
                    level = 'danger'
            else:
                level = 'primary'
        except:
            level = 'danger'
        context[section.name] = {'section': section.name, 'imagelist':ImageList.objects.filter(section__name=section.name)[:3]}
        levels[section.name] = level
    frontview = FrontView.objects.latest()
    return render(request, 'record/record.html', {'context': context, 'frontview': frontview, 'levels': json.dumps(levels)})

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

@csrf_exempt
def side(request):
    form = ImageListForm()
    if request.method == 'POST':
        form = ImageListForm(request.POST, request.FILES)
        # form.save()
        if form.is_valid():
            form.save()
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

