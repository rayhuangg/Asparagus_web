from django.shortcuts import render
from django.http import HttpResponse
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import json
from record.models import ImageList, Section
from monitor.models import Instance, ResultList, Demo

# Create your views here.
def index(request):
    demos = [d for d in Demo.objects.all()] # {{ demolist.name }} form
    demo_range = [ [d.id, d.name] for d in Demo.objects.all() ]
    sections = [ s for s in Section.objects.all()]
    return render(request, 'stats/stats.html', context={'demolist': demos[::-1], 'demorange': demo_range[::-1], 'sections': sections})

def checkRange(request):
    if request.method == 'POST':
        fromValue = request.POST['fromValue']
        untilValue = request.POST['untilValue']
        section = int(request.POST['section'])
        demolist = [ d for d in Demo.objects.all() if int(fromValue) <= d.id <= int(untilValue)]
        # print(fromValue, untilValue, demolist)
        labels = [ d.name for d in demolist ]
        clumps, stalks, spears = [], [], []
        if section == 0:
            for demo in demolist:
                name_demo = demo.name
                num_clump, num_stalk, num_spear = 0, 0, 0
                for result in ResultList.objects.filter(demo__id=demo.id):
                    name_result = result.name
                    for instance in Instance.objects.filter(resultlist__id=result.id):
                        if instance.predicted_class == 'clump':
                            num_clump += 1
                        elif instance.predicted_class == 'stalk':
                            num_stalk += 1
                        elif instance.predicted_class == 'spear':
                            num_spear += 1
                clumps.append(num_clump)
                stalks.append(num_stalk)
                spears.append(num_spear)
        else:
            for demo in demolist:
                name_demo = demo.name
                num_clump, num_stalk, num_spear = 0, 0, 0
                for result in ResultList.objects.filter(demo__id=demo.id).filter(image__section__id=section):
                    name_result = result.name
                    for instance in Instance.objects.filter(resultlist__id=result.id):
                        if instance.predicted_class == 'clump':
                            num_clump += 1
                        elif instance.predicted_class == 'stalk':
                            num_stalk += 1
                        elif instance.predicted_class == 'spear':
                            num_spear += 1
                clumps.append(num_clump)
                stalks.append(num_stalk)
                spears.append(num_spear)
        return HttpResponse(json.dumps({'labels': labels[::-1], 'clumps': clumps[::-1], 'stalks': stalks[::-1], 'spears': spears[::-1]}))
