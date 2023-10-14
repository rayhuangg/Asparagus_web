from django.shortcuts import render
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import ImageList, Section
from .models import Instance, ResultList, Demo
# detectron/demo/demo.py
import argparse
import glob
import multiprocessing as mp
import os
import time
import cv2
import csv
import tqdm
import pytz
import datetime
import pickle
import base64
import json
import numpy as np
from PIL import Image
from datetime import timedelta
from skimage.draw import polygon2mask
from skimage import measure, morphology
from skimage.morphology import skeletonize
from scipy import ndimage
from pycocotools import mask
from plantcv import plantcv as pcv
import pymysql.cursors
from .sql_chiang import thermalTime
import math
from detectron2.config import get_cfg
from detectron2.data.detection_utils import read_image
from detectron2.utils.logger import setup_logger
from skimage import measure, morphology,feature
from detectron.demo.predictor import VisualizationDemo

# Create your views here.
@csrf_exempt
def index(request):
    if request.method == 'POST':
        context = {'section': [], 'image': [], 'instance': []}
        section = request.POST['id']
        demo_id = request.POST['demo']
        context['section'] = section
        resultlist = ResultList.objects.filter(demo__id=demo_id)
        resultlist = resultlist.filter(image__section__name=section)[0]
        image_id = resultlist.image.id
        context['id'] = image_id
        instances = Instance.objects.filter(resultlist=resultlist)
        image = ImageList.objects.get(id=image_id)
        context['image'] = image.image.url
        context['date'] = image.date.astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y.%m.%d %H:%M:%S')
        # calculate scale for each instance
        # scale = []
        # for instance in instances:
        #     if instance.predicted_class == 'bar':
        #         scale.append(instance.width)
        # if scale == []:
        #     scale.append(18)
        # scale = 18/(sum(scale)/len(scale))  ## 20mm / length of pixel
        scales = instances.filter(predicted_class='straw')
        if len(scales) == 0:
            scales = scales | instances.filter(predicted_class='bar')
        if scales:
            context['thermaltime'] = thermalTime(image.date.astimezone(pytz.timezone('Asia/Taipei')))
        for instance in instances:
            if instance.predicted_class != 'straw':
                scale = closest_scale(scales, instance)
                if scale != 0:
                    if scale.predicted_class == 'straw':
                        scale_width = 10 / scale.width ## the width of straw is 10 mm, so
                        scale = 200 / scale.height
                    else:
                        scale_width = 18 / scale.width
                        scale = 150 / scale.height
                else:
                    scale = 0
                    scale_width = 0
            else:
                scale = instance.height
                scale_width = instance.width

            height = instance.height
            width = instance.width
            # context['instance'].append({'class': instance.predicted_class,
            #                             'score': instance.score,
            #                             'bbox': [instance.bbox_xmin, instance.bbox_ymin, instance.bbox_xmax, instance.bbox_ymax],
            #                             'mask': instance.mask,
            #                             'area': cv2.contourArea(cv2.UMat(np.expand_dims(np.array(instance.mask).astype(np.float32), 1))),
            #                             'height': instance.height,
            #                             'width' : instance.width,
            #                             'scale': scale,
            #                             })

            if instance.predicted_class == 'bar' or instance.predicted_class == 'straw'or scale ==0:
                context['instance'].append({'class': instance.predicted_class,
                                            'score': instance.score,
                                            'bbox': [instance.bbox_xmin, instance.bbox_ymin, instance.bbox_xmax, instance.bbox_ymax],
                                            'mask': instance.mask,
                                            'area': cv2.contourArea(cv2.UMat(np.expand_dims(np.array(instance.mask).astype(np.float32), 1))),
                                            'height': height,
                                            'width' : width,
                                            'scale': scale,
                                            })
            else:
                context['instance'].append({'class': instance.predicted_class,
                                            'score': instance.score,
                                            'bbox': [instance.bbox_xmin, instance.bbox_ymin, instance.bbox_xmax, instance.bbox_ymax],
                                            'mask': instance.mask,
                                            'area': cv2.contourArea(cv2.UMat(np.expand_dims(np.array(instance.mask).astype(np.float32), 1))),
                                            'height': height,
                                            'width' : (width/scale)*scale_width,
                                            'scale': scale,
                                            })

        return HttpResponse(json.dumps(context))
    demos = [d for d in Demo.objects.all()] # {{ demolist.name }} form
    demo_range = [ [d.id, d.name] for d in Demo.objects.all()]
    sections = [ s for s in Section.objects.all()]
    return render(request, 'monitor/monitor.html', context={'demolist': demos, 'demorange': demo_range[::-1], 'sections': sections})


def downloadJSON(request, id):
    if request.method == 'POST':
        image = ImageList.objects.get(id=id).image.path
        resultlist = ResultList.objects.filter(image__id=id).latest()
        instances = Instance.objects.filter(resultlist=resultlist)
        img_shape = cv2.imread(image).shape
        img_height, img_width = img_shape[0], img_shape[1]
        with open(image, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode("utf-8")
        content = {
        "version": "4.5.5",
        "flags": {},
        "shapes": [
        ],
        "imagePath": str(id) + '.' + image.split('.')[-1],
        "imageData": img_data,
        "imageHeight": img_height,
        "imageWidth": img_width
        }
        for idx, instance in enumerate(instances):
            if instance.predicted_class == 'clump':
                shape = {
                    "label": "clump",
                    "points": [[instance.bbox_xmin, instance.bbox_ymin], [instance.bbox_xmax, instance.bbox_ymax]],
                    "group_id": idx,
                    "shape_type": "rectangle",
                    "flags": {}
                }
            elif instance.predicted_class == 'stalk' or instance.predicted_class == 'spear':
                mask = instance.mask
                new_mask = []
                if len(instance.mask) > 30:
                    for k in range(0, len(mask), int(len(mask)/30)):
                        new_mask.append(mask[k])
                else:
                    new_mask = mask
                shape = {
                    "label": instance.predicted_class,
                    "points": new_mask,
                    "group_id": idx,
                    "shape_type": "polygon",
                    "flags": {}
                }
            content["shapes"].append(shape)

        return HttpResponse(json.dumps(content, indent=2))
    return HttpResponse(json.dumps({"PAIN": "PEKO"}))


# def downloadexcel(request,total_id):
#     if request.method == 'POST':
#         resultlists = ResultList.objects.filter(demo__id=total_id)
#         section = []
#         #print(resultlists)
#         demolist = [ d for d in Demo.objects.all()]
#         clumps, stalks, spears, bar_section = {} , {} , {} , {}


#         for result in resultlists:
#             name_section = result.image.section.name
#             section.append(name_section)
#             instances = Instance.objects.filter(resultlist__id=result.id)
#             scales = instances.filter(predicted_class='straw')
#             if len(scales) == 0:
#                 scales = scales | instances.filter(predicted_class='bar')
#             if name_section in spears:
#                 pass
#            else:
#                 clumps[name_section] = 0
#                 stalks[name_section] = 0
#                 spears[name_section] = []
#                 bar_section[name_section] = []
#             for instance in instances:
#                 if instance.predicted_class == 'clump':
#                     clumps[name_section] += 1
#                 elif instance.predicted_class == 'stalk':
#                     stalks[name_section] += 1
#                 elif instance.predicted_class == 'bar':
#                     bar_xmid = (instance.bbox_xmax+instance.bbox_xmin)/2
#                     bar_section[name_section].append([bar_xmid])
#                 elif instance.predicted_class == 'spear':
#                     if len(scales) != 0:
#                         scale = closest_scale(scales, instance)
#                         if scale.predicted_class == 'straw' :
#                             # scale = 10 / scale.width
#                             scale = 200 / scale.height
#                             scale_type = 1
#                         else:
#                             scale = 150 / scale.height
#                             # scale = 18 / scale.width
#                             scale_type = 2
#                         #spears[name_section].append(instance.height*scale)
#                     else:
#                         scale = 1 #no sca
#                         scale_type = 0
#

#                     #spears[name_section].append(scale)
#                     area = cv2.contourArea(cv2.UMat(np.expand_dims(np.array(instance.mask).astype(np.float32), 1)))
#                     bbox_xmid = (instance.bbox_xmax+instance.bbox_xmin)/2
#                     # print(scale)
#                     spears[name_section].append([bbox_xmid,area*scale*scale,instance.width*scale,instance.height*scale,scale_type,bbox_xmid])


        #print(spears)
        #print(section)
#         scale_type_dict ={0:'None',1:'Straw',2:'Bar'}
#         response = HttpResponse()
#         response['Content-Disposition'] = "attachment;filename='abc.csv'"
#         writer = csv.writer(response)
#         writer.writerow(['Demo ID:',total_id])
#         writer.writerow([''])
#         writer.writerow(['Section','Spear_ID','Area(mm2)','Width(mm)','Length(mm)','Scale_type','Direction','Position to bar'])
#         for i in range(len(section)):
#             sort_spear = sorted(spears[section[i]])
#             # print((sort_spear))
#             sort_bar = sorted(bar_section[section[i]])
#             # print((sort_bar))
#             for j in (range(len(sort_spear))):
#                 for k in (range(len(sort_bar))):
#                     distance2bar = sort_spear[j][5] - sort_bar[k][0]
#                     if distance2bar > 0:
#                        Direction = 'right'
#                     elif distance2bar < 0:
#                        Direction = 'left'
#                     elif distance2bar == 0:
#                        Direction = 'mid'
#                     writer.writerow([str(section[i]),j+1,round(sort_spear[j][1],2),
#                     round(sort_spear[j][2],2),round(sort_spear[j][3],2),scale_type_dict[sort_spear[j][4]],Direction,abs(distance2bar)])
#                     #writer.writerow( spears[section[i]])

#    return response



def downloadexcel(request,total_id):
    if request.method == 'POST':
        print(total_id)
        resultlists = ResultList.objects.filter(demo__id=total_id)
        section = []
        demolist = [ d for d in Demo.objects.all()]
        clumps, stalks, spears,  bar_section= {} , {}, {}, {}
        # instance_num = 0
        new_result = []
        # print(resultlists)

        target = {}
        for i, result in enumerate(resultlists):
            if result.image.id not in target.keys():
                target[result.image.id] = i
            else:
                if resultlists[target[result.image.id]].id < result.id:
                    target[result.image.id] = i

        for image_id in target.keys():
            result = resultlists[target[image_id]]
            print(result)
        # for result in resultlists:
            name_section = result.image.section.name
            # print(result.image.id)
            section.append(name_section)
            instances =  Instance.objects.filter(resultlist__id=result.id)
            scales = instances.filter(predicted_class='straw')
            # ig, ax = plt.subplots()
            # image = plt.imread("/home/adam/django_asparagus/b21or.jpg")
            # plt.imshow(image)
            if len(scales) == 0:
                scales = scales | instances.filter(predicted_class='bar')
            if name_section in spears:
                pass
            else:
                clumps[name_section] = 0
                stalks[name_section] = 0
                spears[name_section] = []
                bar_section[name_section] = []
            for instance in instances:
                # instance_num += 1
                # print(instance_num)
                if instance.predicted_class == 'clump':
                    clumps[name_section] += 1
                elif instance.predicted_class == 'stalk':
                    stalks[name_section] += 1
                elif instance.predicted_class == 'bar':
                    bar_xmid = (instance.bbox_xmax+instance.bbox_xmin)/2
                    bar_section[name_section].append([bar_xmid])

                elif instance.predicted_class == 'spear':
                    if len(scales) != 0:
                        scale = closest_scale(scales, instance)
                        if scale.predicted_class == 'straw' :
                            width_scale = 10 / scale.width
                            scale = 200 / scale.height
                            scale_type = 1
                        else:
                            width_scale = 18 / scale.width
                            scale = 150 / scale.height
                            #scale = 18 / scale.width
                            scale_type = 2
                        # spears[name_section].append(instance.height*scale)

                    else:
                        scale = 1 #no sca
                        scale_type = 0
                    # spears[name_section].append(scale)
                    area = cv2.contourArea(cv2.UMat(np.expand_dims(np.array(instance.mask).astype(np.float32), 1)))
                    bbox_xmid = (instance.bbox_xmax+instance.bbox_xmin)/2
                    spears[name_section].append([bbox_xmid,area*scale*scale,instance.width*scale,instance.height*scale,scale_type,bbox_xmid])
        # print(clumps)
        # print(stalks)
        # print(spears)
        scale_type_dict ={0:'None',1:'Straw',2:'Bar'}
        response = HttpResponse()
        response['Content-Disposition'] = "attachment;filename='abc.csv'"
        writer = csv.writer(response)
        writer.writerow(['Demo ID:',total_id])
        writer.writerow([''])
        writer.writerow(['Section','Spear_ID','Area(mm2)','Width(mm)','Length(mm)','Scale_type','Direction','Distance to bar(pixs)'])



        for i in range(len(section)):
            sort_spear = sorted(spears[section[i]])
            # print((sort_spear))
            sort_bar = sorted(bar_section[section[i]])
            # print((sort_bar))
            for j in (range(len(sort_spear))):
                for k in (range(len(sort_bar))):
                    distance2bar = sort_spear[j][5] - sort_bar[k][0]
                    if distance2bar > 0:
                       Direction = 'right'
                    elif distance2bar < 0:
                       Direction = 'left'
                    elif distance2bar == 0:
                       Direction = 'mid'
                    writer.writerow([str(section[i]),j+1,round(sort_spear[j][1],2),
                    round(sort_spear[j][2],2),round(sort_spear[j][3],2),scale_type_dict[sort_spear[j][4]],Direction,abs(distance2bar)])
                    # writer.writerow( spears[section[i]])

    return response


def closest_scale(scales, instance):
    """
    This function finds the closest scale to a given instance among a list of scales.

    Parameters:
        scales (list): A list containing multiple scale.
        instance (dict): A dictionary containing information about the target instance.

    Returns:
        dict: The scale from the 'scales' list that is closest to the target instance based on centroid proximity.

    """
    # Calculate the centroid of the target instance
    instance_center = [(instance.bbox_xmax + instance.bbox_xmin)/2, (instance.bbox_ymax + instance.bbox_ymin)/2]
    min_dist = np.inf
    closest_scale = 0

    # Iterate through each scale and find the closest one to the  instance
    for scale in scales:
        mask_scale = np.array(scale.mask)
        scale_center = [np.mean(mask_scale[:, 0]), np.mean(mask_scale[:, 1])]

        # Calculate the squared distance between the centroids
        dist = (instance_center[0]-scale_center[0])**2 + (instance_center[1]-scale_center[1])**2

        # Update the closest scale if the current scale is closer
        if dist < min_dist:
            min_dist = dist
            closest_scale = scale

    return closest_scale


def checkDemoId(request):
    if request.method == 'POST':
        demo_id = request.POST['demo']
        resultlists = ResultList.objects.filter(demo__id=demo_id)
        section = []
        for resultlist in resultlists:
            section.append(resultlist.image.section.name)
        # print(section)
        return HttpResponse(json.dumps({'sections': section}))

def checkRange(request):
    if request.method == 'POST':
        fromValue = request.POST['fromValue']
        untilValue = request.POST['untilValue']
        section = int(request.POST['section'])
        demolist = [ d for d in Demo.objects.all() if int(fromValue) <= d.id <= int(untilValue)]
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


def get_latest():
    url_set = []
    for i in range(1,218):
        try:
            url_set.append([i, ImageList.objects.filter(section__id=i).latest().image.path])
        except:
            pass
    return url_set

def setup_cfg():
    # load config from file and command-line arguments
    cfg = get_cfg()
    cfg.merge_from_file("detectron/output/model_straw.yaml")
    # cfg.merge_from_list(args.opts)
    # Set score_threshold for builtin models
    cfg.MODEL.WEIGHTS = "detectron/output/model_straw.pth"
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = 0.5
    cfg.freeze()
    return cfg

def skeletonization(pred_mask):
    pred_mask = np.asarray(pred_mask) + 0
    skeleton = morphology.skeletonize(pred_mask)
    return skeleton

def straw_detection(path):
    img = cv2.imread(path)
    hue = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[:,:,0]
    sat = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[:,:,1]
    boxes, widths = [], []
    # momo color
    straw_momo = np.ones((len(sat), len(sat[0]))) * [sat > 100] * [img[:, :, 0] > 100] * [hue > 200]
    label_momo = measure.label(straw_momo[0])
    test_momo = {}
    for i in range(len(label_momo)):
        for j in range(len(label_momo[0])):
            try:
                test_momo[label_momo[i][j]] += 1
            except:
                test_momo[label_momo[i][j]] = 1
    test_momo = {k: v for k, v in sorted(test_momo.items(), key=lambda item: item[1], reverse=True)}
    test_momo.pop(0)
    for k, v in test_momo.items():
        # the region larger than 1000
        if v > 1000:
            straw = np.ones((len(sat), len(sat[0]))) * [label_momo == k] *255
            ret, thresh = cv2.threshold(np.float32(straw[0]), 127, 255, 0)
            _, contours, _ = cv2.findContours(np.uint8(thresh), 1, 2)
            areas = []
            for contour in contours:
                areas.append(cv2.contourArea(contour))

            cnt = contours[areas.index(max(areas))]
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            width = min([((box[1][0] - box[0][0])**2 + (box[1][1] - box[0][1])**2)**0.5, ((box[1][0] - box[2][0])**2 + (box[1][1] - box[2][1])**2)**0.5])
            boxes.append(box)
            widths.append(width)
    # blue color
    straw_blue = np.ones((len(sat), len(sat[0]))) * [sat > 150] * [img[:, :, 2] > 100] * [hue > 100]
    label_blue = measure.label(straw_blue[0])
    test_blue = {}
    for i in range(len(label_blue)):
        for j in range(len(label_blue[0])):
            try:
                test_blue[label_blue[i][j]] += 1
            except:
                test_blue[label_blue[i][j]] = 1
    test_blue = {k: v for k, v in sorted(test_blue.items(), key=lambda item: item[1], reverse=True)}
    test_blue.pop(0)
    for k, v in test_blue.items():
        # the region larger than 1000
        if v > 1000:
            straw = np.ones((len(sat), len(sat[0]))) * [label_blue == k] *255
            ret, thresh = cv2.threshold(np.float32(straw[0]), 127, 255, 0)
            _, contours, _ = cv2.findContours(np.uint8(thresh), 1, 2)
            areas = []
            for contour in contours:
                areas.append(cv2.contourArea(contour))
            cnt = contours[areas.index(max(areas))]
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            width = min([((box[1][0] - box[0][0])**2 + (box[1][1] - box[0][1])**2)**0.5, ((box[1][0] - box[2][0])**2 + (box[1][1] - box[2][1])**2)**0.5])
            boxes.append(box)
            widths.append(width)
    return boxes, widths

# Function to handle POST requests when the "demo" button is pressed on the record page.
# Or trigger by the patrol_image_Instant_detect_toggle checkbox
def demo(request):
    """
    This function processes a POST request and handles the data contained within it.

    POST Request Content:
    - 'demo_img_id': A comma-separated list of image IDs representing the images to be detected.
                     If None or "foo," the program will use the 'demo_img_name' to perform detection.
    - 'demo_img_name': A comma-separated list of image names to be used for detection.
    - 'source': Indicates the source of the request, which may be 'scheduled,' 'manual,' or 'patrol.'
                - 'scheduled': Used when detection is needed for data collected throughout the day.
                - 'manual': Enables manual selection of images for detection.
                - 'patrol': Used during robot patrols in the field, where prediction results are saved in a single demo instance.

    Note:
    - The function initializes multiprocessing and sets up logging.
    - It retrieves 'demo_img_id' and 'demo_img_name' parameters from the POST request.
    - Depending on the 'source' parameter, it gathers images differently.
    - For 'scheduled' source, it collects images taken within the last day.
    - For 'manual' source, it collects images specified by 'demo_img_id.'
    - For 'patrol' source, it collects images specified by 'demo_img_id' and manages ongoing patrol sessions.
    - The function performs instance segmentation and stores the results in the database.

    Returns:
    - HttpResponse: A success message indicating the completion of the processing.
    """

    if request.method == 'POST':
        mp.set_start_method("spawn", force=True)
        setup_logger(name="fvcore")
        print('Hello, start inference',flush=True)
        demo_img_id = request.POST.get('demo_img_id', '')
        demo_img_name = request.POST.get('demo_img_name', '')
        try:
            idsDemo = []  # List to store image IDs to be processed

            # If the 'demo_img_id' parameter is not empty and not equal to "foo"
            if demo_img_id and demo_img_id != "foo":
                idsDemo = [int(id.strip()) for id in demo_img_id.split(',') if id.strip()]  # the image id to be detected

        except ValueError:
            idsDemo = []

        if demo_img_name and demo_img_name != "foo":
            name_list = [name.strip() for name in demo_img_name.split(',')]
            images_with_name = ImageList.objects.filter(name__in=name_list)
            idsDemo += [img.id for img in images_with_name]
        # straw = request.POST['straw'] # Straw detection buttom, current not used.(Adam)
        inputs = []


        print("The following picture need to inference:", idsDemo)

        if request.POST['source'] == 'scheduled':
            now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
            oneDayBefore = now - datetime.timedelta(days=1)
            sectiondict = {}
            for img in ImageList.objects.filter(date__range=[oneDayBefore, now]):
                if img.section.name not in sectiondict:
                    sectiondict[img.section.name] = img
                elif img.date > sectiondict[img.section.name].date:
                    sectiondict[img.section.name] = img
            for _, img in sectiondict.items():
                inputs.append([img.id, img.image.path])
            demo_model = Demo(source='scheduled')
            demo_model.save()

        # manual press demo buttom
        elif request.POST['source'] == 'manual':
            imgs = [ImageList.objects.get(id=id) for id in idsDemo]
            sectiondict = {}
            for img in imgs:
                if img.section.name not in sectiondict:
                    sectiondict[img.section.name] = img
                elif img.date > sectiondict[img.section.name].date:
                    sectiondict[img.section.name] = img
            for _, img in sectiondict.items():
                inputs.append([img.id, img.image.path])

            demo_model = Demo(source='manual')
            demo_model.save()

        # "patrol" means the vehicle is moving in the field,
        # continuously uploading and detecting images within the same demo ID.
        elif request.POST['source'] == 'patrol':
            imgs = [ImageList.objects.get(id=id) for id in idsDemo]
            sectiondict = {}
            for img in imgs:
                if img.section.name not in sectiondict:
                    sectiondict[img.section.name] = img
                elif img.date > sectiondict[img.section.name].date:
                    sectiondict[img.section.name] = img
            for _, img in sectiondict.items():
                inputs.append([img.id, img.image.path])

            # FIXME: change to use the photo upload time
            # Check if there is an existing lasting demo with 'patrol' as the source
            latest_demo = Demo.objects.order_by('-date').first()
            if latest_demo:
                # calculate the time between now and lastest patrol demo
                current_time = timezone.now() # django time object
                time_difference = current_time - latest_demo.date
                if latest_demo.source == 'patrol' and time_difference < timedelta(minutes=5):
                    demo_model = latest_demo
                else:
                    # if not, create a new demo object
                    demo_model = Demo.objects.create(source="patrol")
                    demo_model.save()
            else:
                # If no existing 'patrol' demo, create a new one
                demo_model = Demo.objects.create(source="patrol")
                demo_model.save()


        cfg = setup_cfg()
        demo = VisualizationDemo(cfg)
        class_id = {1: 'clump', 2: 'stalk' , 3: 'spear', 4: 'bar', 5:'straw'}
        demo_id = demo_model.id

        for image_id, path in tqdm.tqdm(inputs):
            img = read_image(path, format="BGR")
            predictions, visualized_output = demo.run_on_image(img)
            pred_classes = predictions['instances'].pred_classes.cpu().numpy()
            pred_scores = predictions['instances'].scores.cpu().numpy()
            print(pred_scores, flush=True)
            pred_boxes = np.asarray(predictions["instances"].pred_boxes)
            pred_masks = predictions["instances"].pred_masks.cpu().numpy()
            pred_all = []
            for i in range(len(pred_classes)):
                try:
                    pred_all.append([pred_classes[i], pred_scores[i], pred_boxes[i], pred_masks[i]])
                except:
                    pass
            pred_all = sorted(pred_all, key=lambda x: x[0])

            pred_classes, pred_scores, pred_boxes, pred_masks = [], [], [], []
            for i in range(len(pred_all)):
                pred_classes.append(pred_all[i][0])
                pred_scores.append(pred_all[i][1])
                pred_boxes.append(pred_all[i][2])
                pred_masks.append(pred_all[i][3])

            resultlist = ResultList(image_id=image_id, demo_id=demo_id)
            resultlist.save()
            resultlist_id = resultlist.id

            for i in range(len(pred_classes)):
                try:
                    bbox = pred_boxes[i].cpu().numpy().tolist() ## BBox of instance
                except:
                    bbox = [0 ,0, 0, 0]

                segmentation = pred_masks[i]
                try:
                    segmentation = measure.find_contours(segmentation.T, 0.5)[0].tolist()
                except:
                    segmentation = []

                if pred_classes[i] == 1: # 1 means clump
                    height = bbox[3] - bbox[1]
                    width = bbox[2] - bbox[0]
                elif segmentation == []:
                    continue
                else:
                    new_segmentation = []
                    for j, seg in enumerate(segmentation):
                        if j % 10 == 1:
                            new_segmentation.append(seg)


                    distance_transformation = ndimage.distance_transform_edt(pred_masks[i])
                    # props = measure.regionprops((pred_masks[i].T).astype(np.uint8))
                    props = measure.regionprops((pred_masks[i]).astype(np.uint8))
                    contour = measure.find_contours(pred_masks[i],0.8)

                    height = props[0].major_axis_length
                    width = props[0].minor_axis_length

                    image_size = (1920,1080)
                    angle = props[0].orientation*180/(math.pi)
                    centroid = props[0].centroid
                    mask_t_uint255 = (pred_masks[i].astype(np.uint8)*255)
                    # centroid = (int(centroid[0]),int(centroid[1]))
                    M = cv2.getRotationMatrix2D(centroid,-angle,1.0)
                    rotatedimg = cv2.warpAffine(mask_t_uint255,M,image_size)
                    edges = (feature.canny(rotatedimg).astype(np.uint8)*255)
                    point_left = (int(centroid[0]-width),int(centroid[1]-height/2))
                    point_right = (int(centroid[0]+width),int(centroid[1]+height/2))
                    new_image_crop = rotatedimg[point_left[1]:point_right[1],point_left[0]:point_right[0]]

                    point_left = (int(centroid[0]-width/2),int(centroid[1]-height/2))
                    point_right = (int(centroid[0]+width/2),int(centroid[1]+height/2))
                    new_image_crop1 = rotatedimg[point_left[1]:point_right[1],point_left[0]:point_right[0]]

                    point_left = (int(centroid[0]-width),int(centroid[1]-height/4))
                    point_right = (int(centroid[0]+width),int(centroid[1]+height/4))
                    new_image_crop2 = edges[point_left[1]:point_right[1],point_left[0]:point_right[0]]

                    point_left = (int(centroid[0]-width),int(centroid[1]-height/4))
                    point_right = (int(centroid[0]+width),int(centroid[1]+height/4))
                    new_image_crop2 = edges[point_left[1]:point_right[1],point_left[0]:point_right[0]]

                    try:
                        indices = np.where(new_image_crop2 != [0])
                        indices1 = indices[1]<width
                        indices_left = [ indices[1][i] for i in range(len(indices[1])) if indices[1][i]<width]
                        indices_right = [ indices[1][i] for i in range(len(indices[1])) if indices[1][i]>width]
                        canny_x_start = sum(indices_left)/len(indices_left)
                        canny_x_end = sum(indices_right)/len(indices_right)
                        width = abs(canny_x_end-canny_x_start)
                    except:
                        width = props[0].minor_axis_length


                    skeleton = (skeletonize(pred_masks[i].astype(np.uint8))).astype(np.uint8)
                    height = int(np.sum(skeleton))


                instance = Instance(predicted_class=class_id[pred_classes[i]], score=pred_scores[i], bbox_xmin=bbox[0], bbox_ymin=bbox[1], bbox_xmax=bbox[2], bbox_ymax=bbox[3], mask=segmentation, height=height, width=width, resultlist_id=resultlist_id)
                instance.save()
            # straw detection
            # if straw == 'true':
            #     straw_boxes, straw_widths = straw_detection(path)
            #     for straw_box, straw_width in zip(straw_boxes, straw_widths):
            #         # print(straw_box)
            #         # print(straw_width)
            #         instance = Instance(predicted_class='straw', score=1, mask=straw_box.tolist(), width=straw_width, resultlist_id=resultlist_id)
            #         instance.save()

    return HttpResponse('Success')



# Adam added, unknown reason
def updated(request):
    if request.method == 'POST':
        mp.set_start_method("spawn", force=True)
        setup_logger(name="fvcore")
        # inputs = get_latest()
        demos = [d for d in Demo.objects.all()] # {{ demolist.name }} form
        demo_range = [ [d.id, d.name] for d in Demo.objects.all()]
        sections = [ s for s in Section.objects.all()]
        updated_id = 176
        inputs,inputs_section,inputs_image_list,inputs_image_path,image_id,result_id = [],[],[],[],[],[]
        inputs_section = []
        inputs_image_list = []
        inputs_image_path =[]
        image_id = []
        result_id = []

        # resultlist = ResultList.objects.filter(demo__id=demo_id)
        # resultlist = resultlist.filter(image__section__name=section)[0]
        # image_id = resultlist.image.id
        # for img in ImageList.objects.filter(date__range=[oneDayBefore, now]):
        # name_demo = demo.name
        # image_id = []

        for result in ResultList.objects.filter(demo__id=updated_id):
            name_result = result.image
            image_id.append(result.image.id)
            section_result = name_result.section.name
            result_id.append(result.id)
            # path = result.path
            # inputs.append(name_result)
            inputs_section.append(section_result)
        image_id = set(image_id)
        print(image_id)
        print(max(result_id))
        max_result_id = max(result_id)
        print(max_result_id)

        sectiondict = {}
        imgs = [ImageList.objects.get(id=id) for id in image_id]
        print("imgs : ", imgs )
            # for instance in str(result.id):
            #     print(instance.path)

        for img in imgs:
            if img.section.name not in sectiondict:
                sectiondict[img.section.name] = img
            elif img.date > sectiondict[img.section.name].date:
                sectiondict[img.section.name] = img
        for _, img in sectiondict.items():
            inputs.append([img.id, img.image.path])
        print(inputs)

        cfg = setup_cfg()


        # # print(result_id)



        demo = VisualizationDemo(cfg)
        class_id = {1: 'clump', 2: 'stalk' , 3: 'spear', 4: 'bar', 5:'straw'}
        spear_num = 0
        pro = 0


        for image_id, path in tqdm.tqdm(inputs):
            img = read_image(path, format="BGR")
            start_time = time.time()
            predictions, visualized_output = demo.run_on_image(img)
            # print('finish pred')
            pred_classes = predictions['instances'].pred_classes.cpu().numpy()
            pred_scores = predictions['instances'].scores.cpu().numpy()
            print(pred_classes)
            #try:
            #    pred_boxes = np.asarray(predictions["instances"].pred_boxes.to('cpu'))
            #except:
            #    pass
            pred_boxes = np.asarray(predictions["instances"].pred_boxes)
            #try:
            #    pred_masks = np.asarray(predictions["instances"].pred_masks.to('cpu'))
            #except:
            #    pass
            pred_masks = predictions["instances"].pred_masks.cpu().numpy()

            pred_all = []
            for i in range(len(pred_classes)):
                try:
                    pred_all.append([pred_classes[i], pred_scores[i], pred_boxes[i], pred_masks[i]])
                except:
                    pass
            pred_all = sorted(pred_all, key=lambda x: x[0])

            pred_classes, pred_scores, pred_boxes, pred_masks = [], [], [], []
            for i in range(len(pred_all)):
                pred_classes.append(pred_all[i][0])
                pred_scores.append(pred_all[i][1])
                pred_boxes.append(pred_all[i][2])
                pred_masks.append(pred_all[i][3])

            # print('start resultlist')
            resultlist = ResultList(image_id=image_id, demo_id=updated_id)
            # resultlist.save()
            resultlist_id = resultlist.id

            # print('writing instances')
            for i in range(len(pred_classes)):
                print(class_id[pred_classes[i]])
                try:
                    bbox = pred_boxes[i].cpu().numpy().tolist() ## BBox of instance
                except:
                    bbox = [0 ,0, 0, 0]
                segmentation = pred_masks[i]
                try:
                    segmentation = measure.find_contours(segmentation.T, 0.5)[0].tolist()
                except:
                    segmentation = []
                if pred_classes[i] == 1:
                    height = bbox[3] - bbox[1]
                    width = bbox[2] - bbox[0]
                elif segmentation == []:
                    continue
                else:
                    new_segmentation = []
                    for j, seg in enumerate(segmentation):
                        if j % 10 == 1:
                            new_segmentation.append(seg)
                    image_size = (1920,1080)
                    polygon = np.array(segmentation)
                    straw_mask = polygon2mask(image_size,polygon)
                    props_per = measure.regionprops(straw_mask.astype(np.uint8))
                    straw_mask_t = straw_mask.T
                    props = measure.regionprops(straw_mask_t.astype(np.uint8))
                    straw_mask_t_uint255 = (straw_mask_t.astype(np.uint8)*255)


                    skeleton = (skeletonize(straw_mask_t.astype(np.uint8))).astype(np.uint8)
                    height = int(np.sum(skeleton))
                    # print(height)
                    # cv2.imwrite(str(instance.predicted_class)+'skeleton.jpg', skeleton*255)

                    width =  props[0].minor_axis_length
                    heith =  props[0].major_axis_length


                    angle = props[0].orientation*180/(math.pi)
                    centroid = props_per[0].centroid
                    # centroid = (int(centroid[0]),int(centroid[1]))
                    M = cv2.getRotationMatrix2D(centroid,-angle,1.0)
                    rotatedimg = cv2.warpAffine(straw_mask_t_uint255,M,image_size)
                    edges = (feature.canny(rotatedimg).astype(np.uint8)*255)
                    point_left = (int(centroid[0]-width),int(centroid[1]-heith/2))
                    point_right = (int(centroid[0]+width),int(centroid[1]+heith/2))
                    new_image_crop = straw_mask_t[point_left[1]:point_right[1],point_left[0]:point_right[0]]

                    point_left = (int(centroid[0]-width/2),int(centroid[1]-heith/2))
                    point_right = (int(centroid[0]+width/2),int(centroid[1]+heith/2))
                    new_image_crop1 = edges[point_left[1]:point_right[1],point_left[0]:point_right[0]]

                    point_left = (int(centroid[0]-width),int(centroid[1]-heith/4))
                    point_right = (int(centroid[0]+width),int(centroid[1]+heith/4))
                    new_image_crop2 = edges[point_left[1]:point_right[1],point_left[0]:point_right[0]]

                    # if instance.predicted_class == "spear":
                    #     cv2.imwrite(str(instance.predicted_class)+'image_crop2'+str(i)+'.jpg', new_image_crop2)
                    #     cv2.imwrite(str(instance.predicted_class)+'image_crop1'+str(i)+'.jpg', edges)


                    indices = np.where(new_image_crop2 != [0])
                    indices1 = indices[1]<width
                    indices2 = [ indices[1][i] for i in range(len(indices[1])) if indices[1][i]<width]
                    indices3 = [ indices[1][i] for i in range(len(indices[1])) if indices[1][i]>width]

                    try:
                        canny_x_start = sum(indices2)/len(indices2)
                        canny_x_end = sum(indices3)/len(indices3)
                        # print('width : ',canny_x_end-canny_x_start)
                        cv2.circle(rotatedimg,(int(centroid[0]),int(centroid[1])), 5, (0, 0, 0), -1)
                        width = abs(canny_x_end-canny_x_start)
                    except:
                        width = width
                    # print(instance.predicted_class,width)
                                        # print(class_id[pred_classes[i]],height)

                    # skeleton = (skeletonize(straw_mask_t.astype(np.uint8))).astype(np.uint8)
                    # height = int(np.sum(skeleton))

                    # print(class_id[pred_classes[i]],height)
                    # cv2.imwrite(str(class_id[pred_classes[i]])+'skeleton.jpg', skeleton*255)

                # add updated list
                instance = Instance(predicted_class=class_id[pred_classes[i]], score=pred_scores[i], bbox_xmin=bbox[0], bbox_ymin=bbox[1], bbox_xmax=bbox[2], bbox_ymax=bbox[3], mask=segmentation, height=height, width=width, resultlist_id=resultlist_id)
                instance.save()
                print(max_result_id)
                # adjust list and replace
                # Instance.objects.filter(resultlist_id=max_result_id).update(predicted_class=class_id[pred_classes[i]], score=pred_scores[i], bbox_xmin=bbox[0], bbox_ymin=bbox[1], bbox_xmax=bbox[2], bbox_ymax=bbox[3], mask=segmentation, height=height, width=width)
                # instance.predicted_class = "stalk"
                # instance.save()
                # print(max_result_id,'  ',height,flush=True)

            pro += 1
            with open('monitor/progress_updated.txt', 'w') as progress:
                progress.writelines(str(pro)+' '+str(len(inputs)))


    return HttpResponse('Success')

