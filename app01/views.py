from django.http import JsonResponse,HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from app01.models import Account, Token, Course, CourseDetail,CourseReview,OftenAskedQuestion
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

class MyCouponField(serializers.CharField):
    """
    优惠券序列化
    """
    def get_attribute(self, instance):
        coupon = instance.coupon.all()
        return coupon
    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id':row.id,'name':row.name,'valid_begin_date':row.valid_begin_date,
                        'valid_end_date':row.valid_end_date})
        return ret


class MyCourseChapterField(serializers.CharField):
    """
    课程章节
    """
    def get_attribute(self, instance):
        chapters = instance.coursechapters.all()
        return chapters
    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id':row.id,'chapter':row.chapter,'name':row.name,'summary':row.summary,
                        'pub_date':row.pub_date})
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
    course_type_name = serializers.CharField(source='get_course_type_display')
    level_name =serializers.CharField(source='get_level_display')
    status_name=serializers.CharField(source='get_status_display')
    pub_date = serializers.DateField(format="%Y-%m-%d")
    coupons = MyCouponField()
    coursechapter = MyCourseChapterField()
    erolledreview = serializers.SerializerMethodField()
    # oftenaskedquestion = OftenAskedQuestionField()
    oftenaskedquestion = serializers.SerializerMethodField()

    # reviews=MyCourseReview()
    class Meta:
        model = Course
        fields = ['id','name','course_img','sub_category','course_type_name','degree_course','brief',
                  'pub_date','period','order','attachment_path',
                  'template_id','level_name','status_name','coupons','coursechapter','erolledreview','oftenaskedquestion']
        depth = 4 # 0 10

    def get_erolledreview(self,obj):
        ret =[]
        objs = CourseReview.objects.filter(enrolled_course__course=obj)
        for i in objs:
            ret.append({'id':i.id,'review':i.review})
        return  ret

    def get_oftenaskedquestion(self,obj):
        rett =[]
        objss = OftenAskedQuestion.objects.filter(id=obj.id)
        for i in objss:
            rett.append({'id': i.id, 'question': i.question})
        return rett






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
        # res= {'code': 1000, 'msg': None}
        id=kwargs.get('pk')
        # id=request.GET.get("id")
        course_obj= CourseDetail.objects.filter(course_id=id).first()
        # course_obj= CourseDetail.objects.all().first()
        # print(course_obj)
        ser = CourseDetailSerialize(instance=course_obj, many=False)
        print(ser.data)
        return Response(ser.data)


class CourseListView(APIView):
    def get(self,request,*args,**kwargs):
        # res= {'code': 1000, 'msg': None}
        course_list = Course.objects.exclude(course_type=2)
        ser = CourseSerialize(instance=course_list,many=True)
        return Response(ser.data)

