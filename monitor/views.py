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
import pickle
import base64
import json
import numpy as np
from PIL import Image
from skimage import measure, morphology
from scipy import ndimage
from pycocotools import mask

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
        scale = []
        for instance in instances:
            if instance.predicted_class == 'bar':
                scale.append(instance.width)
        if scale == []:
            scale.append(18)
        scale = 18/(sum(scale)/len(scale))  ## 20mm / length of pixel
        for instance in instances:
            context['instance'].append({'class': instance.predicted_class,
                                        'score': instance.score,
                                        'bbox': [instance.bbox_xmin, instance.bbox_ymin, instance.bbox_xmax, instance.bbox_ymax],
                                        'mask': instance.mask,
                                        'height': instance.height,
                                        'width' : instance.width,
                                        'scale': scale})
                                        
        return HttpResponse(json.dumps(context))
    demos = [d for d in Demo.objects.all()] # {{ demolist.name }} form
    demo_range = [ [d.id, d.name] for d in Demo.objects.all() ]
    sections = [ s for s in Section.objects.all()]
    return render(request, 'monitor/monitor.html', context={'demolist': demos[::-1], 'demorange': demo_range[::-1], 'sections': sections})

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
    for i in range(1,145):
        try:
            url_set.append([i, ImageList.objects.filter(section__id=i).latest().image.path])
        except:
            pass
    return url_set

def setup_cfg():
    # load config from file and command-line arguments
    cfg = get_cfg()
    cfg.merge_from_file("detectron/configs/COCO-InstanceSegmentation/mask_rcnn_X_101_32x8d_FPN_3x.yaml")
    # cfg.merge_from_list(args.opts)
    # Set score_threshold for builtin models
    cfg.MODEL.WEIGHTS = "detectron/output/model_0269999.pth"
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = 0.5
    cfg.freeze()
    return cfg

def skeletonization(pred_mask):
    pred_mask = np.asarray(pred_mask) + 0
    skeleton = morphology.skeletonize(pred_mask)
    return skeleton

def demo(request):
    if request.method == 'POST':
        mp.set_start_method("spawn", force=True)
        setup_logger(name="fvcore")
        inputs = get_latest()
        cfg = setup_cfg()

        demo = VisualizationDemo(cfg)

        class_id = {1: 'clump', 2: 'stalk' , 3: 'spear', 4: 'bar'}

        demo_model = Demo()
        demo_model.save()

        with open('monitor/progress.txt', 'w') as progress:
            progress.writelines('0 0')
        pro = 0
        for sec_id, path in tqdm.tqdm(inputs):
            # print('start')
            img = read_image(path, format="BGR")
            start_time = time.time()
            predictions, visualized_output = demo.run_on_image(img)
            # print('finish pred')
            pred_classes = predictions['instances'].pred_classes.cpu().numpy()
            pred_scores = predictions['instances'].scores.cpu().numpy()
            pred_boxes = np.asarray(predictions["instances"].pred_boxes.to('cpu'))
            # pred_boxes = np.asarray(predictions["instances"].pred_boxes)
            pred_masks = np.asarray(predictions["instances"].pred_masks.to('cpu'))
            # pred_masks = predictions["instances"].pred_masks.cpu().numpy()

            pred_all = []
            for i in range(len(pred_classes)):
                pred_all.append([pred_classes[i], pred_scores[i], pred_boxes[i], pred_masks[i]])
            pred_all = sorted(pred_all, key=lambda x: x[0])

            pred_classes, pred_scores, pred_boxes, pred_masks = [], [], [], []
            for i in range(len(pred_all)):
                pred_classes.append(pred_all[i][0])
                pred_scores.append(pred_all[i][1])
                pred_boxes.append(pred_all[i][2])
                pred_masks.append(pred_all[i][3])

            # print('start resultlist')
            image_id = ImageList.objects.filter(section_id=sec_id).latest().id
            resultlist = ResultList(image_id=image_id, demo_id=Demo.objects.all().latest().id)
            resultlist.save()
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
                    segmentation = new_segmentation
                    skeleton = skeletonization(pred_masks[i]).tolist()
                    height = np.count_nonzero(skeleton) ## Height of instance
                    distance_transformation = ndimage.distance_transform_edt(pred_masks[i])
                    widths = []
                    for j, row in enumerate(skeleton):
                        for k, p in enumerate(row):
                            if p:
                                widths.append(distance_transformation[j, k])
                    width = round((sum(widths)/len(widths)), 2) ## Width of instance
                
                instance = Instance(predicted_class=class_id[pred_classes[i]], score=pred_scores[i], bbox_xmin=bbox[0], bbox_ymin=bbox[1], bbox_xmax=bbox[2], bbox_ymax=bbox[3], mask=segmentation, height=height, width=width, resultlist_id=ResultList.objects.all().latest().id)
                instance.save()
            pro += 1
            with open('monitor/progress.txt', 'w') as progress:
                progress.writelines(str(pro)+' '+str(len(inputs)))
    return HttpResponse('Success')