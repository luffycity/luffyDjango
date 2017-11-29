from django.http import JsonResponse
from django.shortcuts import render,HttpResponse
from rest_framework.views import APIView
from app01.models import Account, Token, Course, CourseDetail
from app01.utils.auth import LuffyAuthentication
from app01.utils.commons import gen_token
from django.core import serializers
from app01.utils.throttle import LuffyAnonRateThrottle, LuffyUserRateThrottle
from rest_framework import serializers
from rest_framework.response import Response
from app01.utils.permission import LuffyPermission
import json

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

class MyField(serializers.CharField):
    '''get all teacher'''

    def get_attribute(self, instance):
        teacher_list = instance.teachers.all()
        return teacher_list

    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id':row.id,'name':row.name})
        return ret

class MyPricefield(serializers.CharField):
    '''get all price_policy'''
    def get_attribute(self, instance):
        price_policy = instance.course.price_policy.all()
        return  price_policy
    def to_representation(self, value):
        ret =[]
        for row in value:
            ret.append({'id':row.id,'valid_period':row.get_valid_period_display(),'price':row.price})
        return ret

class CourseSerialize(serializers.ModelSerializer):
    '''课程序列化'''

    level_name =serializers.CharField(source='get_level_display')

    class Meta:
        model = Course
        fields = ['id','name','course_img','brief','level_name']

class CourseDetailSerialize(serializers.ModelSerializer):
    '''课程详细序列化'''
    # recommends=MyField()
    # recommends=serializers.CharField(source='recommend_courses.all')
    teacherss=MyField()
    courseprices=MyPricefield()
    class Meta:
        model = CourseDetail

        fields =['id','course','hours','course_slogan','video_brief_link','why_study',
                 'what_to_study_brief','career_improvement','prerequisite','teacherss',
                 'courseprices']
        # depth = 3 # 0 10

class CourseDetailView(APIView):
    '''课程视图'''
    authentication_classes = [LuffyAuthentication, ]

    def get(self, request, *args, **kwargs):
        # res= {'code': 1000, 'msg': None, 'data':None}
        uid=request.GET.get("id")
        # course_obj= CourseDetail.objects.filter(course=id).first()
        course_obj= CourseDetail.objects.filter(pk=uid).first()
        ser = CourseDetailSerialize(instance=course_obj, many=False)
        return Response(ser.data)

class CourseListView(APIView):
    '''课程列表视图'''
    def get(self,request,*args,**kwargs):
        # res= {'code': 1000, 'msg': None}
        course_list = Course.objects.exclude(course_type=2)
        ser = CourseSerialize(instance=course_list,many=True)
        return Response(ser.data)

class RedisHelper(object):
    '''redis助手'''
    def __new__(cls, *args, **kwargs):
        '''
        单例模式
        :param args: 
        :param kwargs: 
        :return: 
        '''
        if not hasattr(cls,'instance'):
            cls.instance = super(RedisHelper,cls).__new__(cls)
        return cls.instance

    def __init__(self):
        '''初始化创建连接池'''
        import redis
        pool = redis.ConnectionPool(host='47.95.220.106', port=6379)
        conn = redis.Redis(connection_pool=pool)
        self.conn = conn

    def get(self,name,k):
        '''
        获取数据
        '''
        return self.conn.hget(name,k)

    def set(self, name, k, v):
        '''写入数据'''
        return self.conn.hset(name, k, v)

    def delete(self, name, k):
        '''删除数据'''
        self.conn.hdel(name,k)


















