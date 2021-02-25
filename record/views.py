from django.shortcuts import render, reverse, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from .models import ImageList, FrontView
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
    row = ['A', 'B', 'C', 'D', 'E', 'F']
    col = [1, 2, 3, 4, 5, 6, 7, 8]
    context = {}
    levels = {}
    now = datetime.datetime.now(datetime.timezone.utc)
    for r in row:
        for c in col:
            try:
                latest_img = ImageList.objects.filter(section__name=r+str(c))[0]
                timedelta = now - latest_img.date
                if timedelta.days >= 2:
                    level = 'warning'
                    if timedelta.days >= 4:
                        level = 'danger'
                else:
                    level = 'primary'
            except:
                level = 'danger'
            context[r+str(c)] = {'section': r+str(c), 'imagelist':ImageList.objects.filter(section__name=r+str(c))[:4]}
            levels[r+str(c)] = level
    frontview = FrontView.objects.latest
    return render(request, 'record/record.html', {'context': context, 'frontview': frontview, 'levels': json.dumps(levels)})



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

