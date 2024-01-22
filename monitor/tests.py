from django.test import TestCase
# from django.utils import timezone
# from .models import Demo, ResultList, Instance
# from record.models import ImageList

# class DemoModelTest(TestCase):
#     def test_demo_str_representation(self):
#         demo = Demo.objects.create(name='TestDemo', date=timezone.now(), source='scheduled')
#         self.assertEqual(str(demo), f'TestDemo_{demo.id}')

# class ResultListModelTest(TestCase):
#     def test_resultlist_str_representation(self):
#         image = ImageList.objects.create(name='TestImage', section_id=25)  # 使用 record_section 表中有效的 section_id 值
#         demo = Demo.objects.create(name='TestDemo', date=timezone.now(), source='scheduled')
#         resultlist = ResultList.objects.create(name='TestResultList', date=timezone.now(), image=image, demo=demo)
#         self.assertEqual(str(resultlist), f'TestResultList_{resultlist.id}')

# class InstanceModelTest(TestCase):
#     def test_instance_str_representation(self):
#         image = ImageList.objects.create(name='TestImage', section_id=25)  # Replace 1 with a valid section_id
#         demo = Demo.objects.create(name='TestDemo', date=timezone.now(), source='scheduled')
#         resultlist = ResultList.objects.create(name='TestResultList', date=timezone.now(), image=image, demo=demo)
#         instance = Instance.objects.create(
#             predicted_class='clump',
#             score=0.9,
#             bbox_xmin=0,
#             bbox_ymin=0,
#             bbox_xmax=100,
#             bbox_ymax=100,
#             mask={},
#             resultlist=resultlist
#         )
#         self.assertEqual(str(instance), 'clump')
