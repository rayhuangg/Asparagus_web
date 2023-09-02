from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import json
from record.models import ImageList, Section
from monitor.models import Instance, ResultList, Demo
from monitor.views import thermalTime, closest_scale
import pytz

# Create your views here.
def index(request):
    demos = [d for d in Demo.objects.all()] # {{ demolist.name }} form
    demo_range = [ [d.id, d.name, d.date.astimezone(pytz.timezone('Asia/Taipei')).strftime('%B %d, %Y, %I:%M %p')] for d in Demo.objects.all() ]
    sections = [ s for s in Section.objects.all()]
    return render(request, 'stats/stats.html', context={'demolist': demos, 'demorange': demo_range[::-1], 'sections': sections, 'thermaltimerange': [i for i in range(24, 0, -1)]})

# def checkRange(request):
#     if request.method == 'POST':
#         fromValue = request.POST['fromValue']
#         untilValue = request.POST['untilValue']
#         section = int(request.POST['section'])
#         demolist = [ d for d in Demo.objects.all() if int(fromValue) <= d.id <= int(untilValue)]
#         # print(fromValue, untilValue, demolist)
#         labels = [ d.name for d in demolist ]
#         clumps, stalks, spears = [], [], []
#         if section == 0:
#             for demo in demolist:
#                 name_demo = demo.name
#                 num_clump, num_stalk, num_spear = 0, 0, 0
#                 for result in ResultList.objects.filter(demo__id=demo.id):
#                     name_result = result.name
#                     for instance in Instance.objects.filter(resultlist__id=result.id):
#                         if instance.predicted_class == 'clump':
#                             num_clump += 1
#                         elif instance.predicted_class == 'stalk':
#                             num_stalk += 1
#                         elif instance.predicted_class == 'spear':
#                             num_spear += 1
#                 clumps.append(num_clump)
#                 stalks.append(num_stalk)
#                 spears.append(num_spear)
#         else:
#             for demo in demolist:
#                 name_demo = demo.name
#                 num_clump, num_stalk, num_spear = 0, 0, 0
#                 for result in ResultList.objects.filter(demo__id=demo.id).filter(image__section__id=section):
#                     name_result = result.name
#                     for instance in Instance.objects.filter(resultlist__id=result.id):
#                         if instance.predicted_class == 'clump':
#                             num_clump += 1
#                         elif instance.predicted_class == 'stalk':
#                             num_stalk += 1
#                         elif instance.predicted_class == 'spear':
#                             num_spear += 1
#                 clumps.append(num_clump)
#                 stalks.append(num_stalk)
#                 spears.append(num_spear)
#         return HttpResponse(json.dumps({'labels': labels[::-1], 'clumps': clumps[::-1], 'stalks': stalks[::-1], 'spears': spears[::-1]}))

def checkRange(request):
    if request.method == 'POST':
        fromValue = request.POST['fromValue']
        untilValue = request.POST['untilValue']
        demolist = [ d for d in Demo.objects.all() if int(fromValue) <= d.id <= int(untilValue)]
        resultlist = []
        for demo in demolist:
            for re in ResultList.objects.filter(demo__id=demo.id):
                resultlist.append(re)
        if fromValue == untilValue:
            print(resultlist[0])
            date = resultlist[0].image.date.astimezone(pytz.timezone('Asia/Taipei'))
            thermaltime = thermalTime(date)
        else:
            thermaltime = None
        clumps, stalks, spears = {}, {}, {}

        for result in resultlist:
            name_section = result.image.section.name
            instances = Instance.objects.filter(resultlist__id=result.id)
            scales = instances.filter(predicted_class='straw')
            if len(scales) == 0:
                scales = scales | instances.filter(predicted_class='bar')
            if name_section in spears:
                pass
            else:
                clumps[name_section] = 0
                stalks[name_section] = 0
                spears[name_section] = []
            for instance in instances:
                if instance.predicted_class == 'clump':
                    clumps[name_section] += 1
                elif instance.predicted_class == 'stalk':
                    stalks[name_section] += 1
                elif instance.predicted_class == 'spear':
                    if len(scales) != 0:
                        scale = closest_scale(scales, instance)
                        scale = 10 / scale.width if scale.predicted_class == 'straw' else 18 / scale.width
                        spears[name_section].append(instance.height)
                    else:
                        spears[name_section].append(0)

        return HttpResponse(json.dumps({'clumps': clumps, 'stalks': stalks, 'spears': spears, 'thermaltime': thermaltime}))