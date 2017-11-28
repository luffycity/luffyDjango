from django.http import JsonResponse,HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from app01.models import Account, Token, Course, CourseDetail
from app01.utils.auth import LuffyAuthentication
from app01.utils.commons import gen_token
from django.core import serializers

import json

from app01.utils.permission import LuffyPermission
from app01.utils.throttle import LuffyAnonRateThrottle, LuffyUserRateThrottle


class AuthView(APIView):
    """
    认证相关视图
    """
    def post(self,request,*args,**kwargs):
        """
        用户登录功能
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret = {'code': 1000, 'msg': None}
        username = request.data.get('username')
        password = request.data.get('password')
        user_obj = Account.objects.filter(username=username, password=password).first()
        if user_obj:
            tk =str(gen_token(username))
            Token.objects.update_or_create(user=user_obj, defaults={'tk': tk})
            ret['code'] = 1001
            ret['token'] = tk
            ret['username'] = username
        else:
            ret['msg'] = "用户名或密码错误"
        return JsonResponse(ret)

class IndexView(APIView):
    """
    用户认证
        http://127.0.0.1:8001/v1/index/?tk=sdfasdfasdfasdfasdfasdfthrottle.py
        获取用户传入的Token

    首页限制：request.user
        匿名：5/m
        用户：10/m
    """
    authentication_classes = [LuffyAuthentication,]
    throttle_classes = [LuffyAnonRateThrottle,LuffyUserRateThrottle]
    def get(self,request,*args,**kwargs):
        return HttpResponse('首页')

from rest_framework import serializers
from rest_framework.response import Response


class MyField(serializers.CharField):
    def get_attribute(self, instance):
        teacher_list = instance.teachers.all()
        return teacher_list

    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id':row.id,'name':row.name})

        return ret

class MyPricefield(serializers.CharField):
    def get_attribute(self, instance):
        price_policy = instance.course.price_policy.all()
        return  price_policy
    def to_representation(self, value):
        ret =[]
        for row in value:
            ret.append({'id':row.id,'valid_period':row.get_valid_period_display(),'price':row.price})
        return ret


class CourseSerialize(serializers.ModelSerializer):
    level_name =serializers.CharField(source='get_level_display')

    class Meta:
        model = Course
        fields = ['id','name','course_img','sub_category','course_type','degree_course','brief',
                  'level','pub_date','period','order','attachment_path','status','template_id','level_name']
        # depth = 3 # 0 10
class CourseDetailSerialize(serializers.ModelSerializer):
    # recommends=serializers.CharField(source='recommend_courses.all')
    teacherss=MyField()
    courseprices=MyPricefield()
    # recommends=MyField()
    class Meta:
        model = CourseDetail

        fields =['id','course','hours','course_slogan','video_brief_link','why_study',
                 'what_to_study_brief','career_improvement','prerequisite','teacherss',
                 'courseprices']
        depth = 3 # 0 10

class CourseView(APIView):
    authentication_classes = [LuffyAuthentication, ]
    # permission_classes = [LuffyPermission,]
    # throttle_classes = [LuffyAnonRateThrottle, LuffyUserRateThrottle]

    def get(self, request, *args, **kwargs):
        res= {'code': 1000, 'msg': None}
        # id=request.GET.get("id")
        # course_obj= CourseDetail.objects.filter(course=id).first()
        course_obj= CourseDetail.objects.all().first()
        print(course_obj)
        ser = CourseDetailSerialize(instance=course_obj, many=False)
        return Response(ser.data)


class CourseListView(APIView):
    def get(self,request,*args,**kwargs):
        res= {'code': 1000, 'msg': None}
        course_list = Course.objects.exclude(course_type=2)
        ser = CourseSerialize(instance=course_list,many=True)
        return Response(ser.data)

