from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from app01.models import Account, Token, Course, CourseDetail
from app01.utils.auth import LuffyAuthentication
from app01.utils.commons import gen_token
from django.core import serializers
from app01.utils.throttle import LuffyAnonRateThrottle, LuffyUserRateThrottle
from rest_framework import serializers
from rest_framework.response import Response
from app01 import models
from app01.utils.permission import LuffyPermission
import json


class AuthView(APIView):
    """
    认证相关视图
    """

    def post(self, request, *args, **kwargs):
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
            tk = str(gen_token(username))
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
    authentication_classes = [LuffyAuthentication, ]
    throttle_classes = [LuffyAnonRateThrottle, LuffyUserRateThrottle]

    def get(self, request, *args, **kwargs):
        return HttpResponse('首页')


class MyField(serializers.CharField):
    '''get all teacher'''

    def get_attribute(self, instance):
        teacher_list = instance.teachers.all()
        return teacher_list

    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id': row.id, 'name': row.name})
        return ret


class MyPricefield(serializers.CharField):
    '''get all price_policy'''

    def get_attribute(self, instance):
        price_policy = instance.course.price_policy.all()
        return price_policy

    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id': row.id, 'valid_period': row.get_valid_period_display(), 'price': row.price})
        return ret


class CourseSerialize(serializers.ModelSerializer):
    '''课程序列化'''

    level_name = serializers.CharField(source='get_level_display')

    class Meta:
        model = Course
        fields = ['id', 'name', 'course_img', 'brief', 'level_name']


class CourseDetailSerialize(serializers.ModelSerializer):
    '''课程详细序列化'''
    # recommends=MyField()
    # recommends=serializers.CharField(source='recommend_courses.all')
    teacherss = MyField()
    courseprices = MyPricefield()
    course_name = serializers.CharField(source='course.name')

    class Meta:
        model = CourseDetail
        fields = ['id', 'course', 'course_name', 'hours', 'course_slogan', 'video_brief_link', 'why_study',
                  'what_to_study_brief', 'career_improvement', 'prerequisite', 'teacherss',
                  'courseprices']
        # depth = 3 # 0 10


class CourseDetailView(APIView):
    '''课程视图'''
    authentication_classes = [LuffyAuthentication, ]

    def get(self, request, *args, **kwargs):
        # res= {'code': 1000, 'msg': None, 'data':None}

        cid = kwargs.get('course_id')
        # course_obj= CourseDetail.objects.filter(course=id).first()
        course_obj = CourseDetail.objects.filter(pk=cid).first()
        ser = CourseDetailSerialize(instance=course_obj, many=False)
        return Response(ser.data)


class CourseListView(APIView):
    '''课程列表视图'''

    def get(self, request, *args, **kwargs):
        # res= {'code': 1000, 'msg': None}
        course_list = Course.objects.exclude(course_type=2)
        ser = CourseSerialize(instance=course_list, many=True)
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
        if not hasattr(cls, 'instance'):
            cls.instance = super(RedisHelper, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        '''初始化创建连接池'''
        import redis
        pool = redis.ConnectionPool(host='47.95.220.106', port=6379)
        conn = redis.Redis(connection_pool=pool)
        self.conn = conn

    def get(self, name, k):
        '''
        获取数据
        '''
        return self.conn.hget(name, k)

    def set(self, name, k, v):
        '''写入数据'''
        return self.conn.hset(name, k, v)

    def delete(self, name, k):
        '''删除数据'''
        self.conn.hdel(name, k)


class ShoppingCar(APIView):
    authentication_classes = [LuffyAuthentication, ]

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):

        response_msg = {'code': 1000, 'data': None, 'error_msg': None}
        # 如果没有登录
        if not request.user:
            response_msg['code'] = 1001
            response_msg['error_msg'] = '请先登录后再进行操作'
            return HttpResponse(json.dumps(response_msg))

        course_detail_id = request.data.get('course_id')
        policy_id = request.data.get('period_id')
        course_detail_obj = models.CourseDetail.objects.filter(pk=course_detail_id).first()
        policy_obj = course_detail_obj.course.price_policy.filter(pk=policy_id).first()

        '''
        data = {
            '课程ID': {
                "course_name": "商品课名称",
                "img": "商品课对应的图片路径",
                "select_price_period_id": "勾选的商品课id",
                "select_price_period_price": "勾选的商品课价格",
                '已选策略ID':'',
                '所有策略ID'：[
                    {'id': 1, name: '1个月', price: '9.9'},
                    {'id': 2, name: '3个月', price: '19.9'},
        ]},
        '''
        # 如果验证成功
        if policy_obj and course_detail_obj:
            course_obj = course_detail_obj.course
            policy_list = course_obj.price_policy.all()

            data = {
                course_obj.id:{
                    "course_name":course_obj.name,
                    "img":course_obj.course_img,
                    "price_period_id":policy_obj.id,
                    "price_policy":policy_obj.price,
                    "price_policy_all_id":[]
                }
            }

            # 添加全部的价格策略
            for obj in policy_list:
                temp = {}
                temp['id'] = obj.id
                temp['period'] = obj.get_valid_period_display()
                temp['price'] = obj.price
                data[course_obj.id]["price_policy_all_id"].append(temp)

            # redis写入操作
            try:
                redis_helper = RedisHelper()
                user_id = request.user.id
                goods_data = redis_helper.get('luffy_car', user_id)
                if goods_data:
                    goods_dict = json.loads(goods_data.decode('utf-8'))
                    goods_dict[str(course_obj.id)] = data[course_obj.id]
                    redis_helper.set('luffy_car', user_id, json.dumps(goods_dict))
                    response_msg['data'] = '课程添加成功'
                else:
                    redis_helper.set('luffy_car', user_id, json.dumps(data))
                    response_msg['data'] = '课程添加成功'
            except ConnectionError as e:
                response_msg['code'] = 1001
                response_msg['error_msg'] = '数据存储失败'
            except Exception as e:
                response_msg['code'] = 1001
                response_msg['error_msg'] = '数据存储失败'

        return HttpResponse('...')


    def put(self, request, *args, **kwargs):
        pass

    def delete(self, request, *args, **kwargs):
        pass