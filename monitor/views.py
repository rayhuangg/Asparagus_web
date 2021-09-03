from django.shortcuts import render
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
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
from skimage import measure, morphology
from scipy import ndimage
from pycocotools import mask
from plantcv import plantcv as pcv

from detectron2.config import get_cfg
from detectron2.data.detection_utils import read_image
from detectron2.utils.logger import setup_logger

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
        # calculate scale for each instance
        # scale = []
        # for instance in instances:
        #     if instance.predicted_class == 'bar':
        #         scale.append(instance.width)
        # if scale == []:
        #     scale.append(18)
        # scale = 18/(sum(scale)/len(scale))  ## 20mm / length of pixel
        scales = instances.filter(predicted_class='straw')
        for instance in instances:
            if instance.predicted_class != 'straw':
                scale = closest_scale(scales, instance)
                if scale != 0:
                    scale = 10 / scale.width ## the width of straw is 18 mm, so 
                else:
                    scale = 0
            else:
                scale = instance.width
            context['instance'].append({'class': instance.predicted_class,
                                        'score': instance.score,
                                        'bbox': [instance.bbox_xmin, instance.bbox_ymin, instance.bbox_xmax, instance.bbox_ymax],
                                        'mask': instance.mask,
                                        'area': cv2.contourArea(cv2.UMat(np.expand_dims(np.array(instance.mask).astype(np.float32), 1))),
                                        'height': instance.height,
                                        'width' : instance.width,
                                        'scale': scale})
                                        
        return HttpResponse(json.dumps(context))
    demos = [d for d in Demo.objects.all()] # {{ demolist.name }} form
    demo_range = [ [d.id, d.name] for d in Demo.objects.all() ]
    sections = [ s for s in Section.objects.all()]
    return render(request, 'monitor/monitor.html', context={'demolist': demos[::-1], 'demorange': demo_range[::-1], 'sections': sections})

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

def closest_scale(scales, instance):
    c_instance = [ (instance.bbox_xmax + instance.bbox_xmin)/2, (instance.bbox_ymax + instance.bbox_ymin)/2]
    max_dist = np.inf
    max_scale = 0
    for scale in scales:
        mask_scale = np.array(scale.mask)
        c_scale = [np.mean(mask_scale[:, 0]), np.mean(mask_scale[:, 1])]
        dist = (c_instance[0]-c_scale[0])**2 + (c_instance[1]-c_scale[1])**2
        if dist < max_dist:
            max_dist = dist
            max_scale = scale
    return max_scale


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
    cfg.merge_from_file("detectron/output/journal.yaml")
    # cfg.merge_from_list(args.opts)
    # Set score_threshold for builtin models
    cfg.MODEL.WEIGHTS = "detectron/output/journal.pth"
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
        # region larger than 1000
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
        # region larger than 1000
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


def demo(request):
    if request.method == 'POST':
        mp.set_start_method("spawn", force=True)
        setup_logger(name="fvcore")
        # inputs = get_latest()
        idsDemo = [ int(id) for id in request.POST['demo'].split(',')]
        straw = request.POST['straw']
        inputs = []
        if request.POST['source'] == 'scheduled':
            now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
            oneDayBefore = now - datetime.timedelta(days=1)
            for img in ImageList.objects.filter(date__range=[oneDayBefore, now]):
                inputs.append([img.id, img.image.path])
            demo_model = Demo(source='scheduled')
        else:
            for id in idsDemo:
                img = ImageList.objects.get(id=id)
                inputs.append([id, img.image.path])
            demo_model = Demo(source='manual')
        cfg = setup_cfg()
        

        demo = VisualizationDemo(cfg)

        class_id = {1: 'clump', 2: 'stalk' , 3: 'spear', 4: 'bar'}

        demo_model.save()
        demo_id = demo_model.id

        with open('monitor/progress.txt', 'w') as progress:
            progress.writelines('0 0')
        pro = 0
        for image_id, path in tqdm.tqdm(inputs):
            # print('start')
            img = read_image(path, format="BGR")
            start_time = time.time()
            predictions, visualized_output = demo.run_on_image(img)
            # print('finish pred')
            pred_classes = predictions['instances'].pred_classes.cpu().numpy()
            pred_scores = predictions['instances'].scores.cpu().numpy()
            # try:
            #     pred_boxes = np.asarray(predictions["instances"].pred_boxes.to('cpu'))
            # except:
            #     pass
            pred_boxes = np.asarray(predictions["instances"].pred_boxes)
            # try:
            #     pred_masks = np.asarray(predictions["instances"].pred_masks.to('cpu'))
            # except:
            #     pass
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
            resultlist = ResultList(image_id=image_id, demo_id=demo_id)
            resultlist.save()
            resultlist_id = resultlist.id
            # print('writing instances')
            for i in range(len(pred_classes)):
                # print(class_id[pred_classes[i]])
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
                    # segmentation = new_segmentation
                    # skeleton = skeletonization(pred_masks[i]).tolist()
                    # height = np.count_nonzero(skeleton) ## Height of instance
                    distance_transformation = ndimage.distance_transform_edt(pred_masks[i])
                    widths = []
                    # for j, row in enumerate(skeleton):
                    #     for k, p in enumerate(row):
                    #         if p:
                    #             widths.append(distance_transformation[j, k])
                    # width = round((sum(widths)/len(widths)), 2) ## Width of instance
                    for row in distance_transformation:
                        width = max(row)
                        if width != 0:
                            widths.append(width)
                    width = max(widths)
                    # skeleton = pcv.morphology.skeletonize(mask=pred_masks[i])
                    props = measure.regionprops(pred_masks[i].astype(np.uint8))
                    height = props[0].major_axis_length
                    # segmented_img, obj = pcv.morphology.segment_skeleton(skel_img=skeleton)
                    # labeled_img = pcv.morphology.segment_path_length(segmented_img=segmented_img, objects=obj, label="default")
                    # path_lengths = pcv.outputs.observations['default']['segment_path_length']['value']
                    # height = max(path_lengths)
                
                instance = Instance(predicted_class=class_id[pred_classes[i]], score=pred_scores[i], bbox_xmin=bbox[0], bbox_ymin=bbox[1], bbox_xmax=bbox[2], bbox_ymax=bbox[3], mask=segmentation, height=height, width=width, resultlist_id=resultlist_id)
                instance.save()
            # straw detection
            if straw == 'true':
                straw_boxes, straw_widths = straw_detection(path)
                for straw_box, straw_width in zip(straw_boxes, straw_widths):
                    # print(straw_box)
                    # print(straw_width)
                    instance = Instance(predicted_class='straw', score=1, mask=straw_box.tolist(), width=straw_width, resultlist_id=resultlist_id)
                    instance.save()

            pro += 1
            with open('monitor/progress.txt', 'w') as progress:
                progress.writelines(str(pro)+' '+str(len(inputs)))
    return HttpResponse('Success')
