from django.http import JsonResponse,HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from app01.models import Account,Token,Course
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
    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = "http://127.0.0.1:8080"
        response['Access-Control-Allow-Methods'] = "PUT,GET,POST"
        response['Access-Control-Allow-Headers'] = "Authorization,Origin, X-Requested-With, Content-Type, Accept"
        # response['Access-Control-Allow-Credentials']="true"
        # response['Access-Control-Allow-Headers'] = "xxx"
        return response
    def post(self,request,*args,**kwargs):
        """
        用户登录功能
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        res_dic = {'code': 1000, 'msg': None}
        username = request.data.get('username')
        password = request.data.get('password')
        user_obj = Account.objects.filter(username=username, password=password).first()
        if user_obj:
            tk =str(gen_token(username))
            Token.objects.update_or_create(user=user_obj, defaults={'tk': tk})
            res_dic['code'] = 1001
            res_dic['token'] = tk
            res_dic['username'] = username
        else:
            res_dic['msg'] = "用户名或密码错误"
        res=HttpResponse(json.dumps(res_dic))
        res['Access-Control-Allow-Origin'] = "http://127.0.0.1:8080"
        res['Access-Control-Allow-Headers'] = "Authorization,Origin, X-Requested-With, Content-Type, Accept"
        # res['Access-Control-Allow-Credentials']="true"
        return res

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
class CourseSerialize(serializers.ModelSerializer):
    # user = serializers.CharField(min_length=6)
    # pwd = serializers.CharField(validators=[PasswordValidator(666), ])
    # ug = serializers.HyperlinkedIdentityField(view_name='xxxx')
    class Meta:
        model = Course
        fields = "__all__"
        depth = 2 # 0 10

class CourseView(APIView):
    authentication_classes = [LuffyAuthentication, ]
    # permission_classes = [LuffyPermission,]
    # throttle_classes = [LuffyAnonRateThrottle, LuffyUserRateThrottle]

    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = "http://127.0.0.1:8080"
        response['Access-Control-Allow-Methods'] = "PUT,GET,POST"
        response['Access-Control-Allow-Headers'] = "Authorization,Origin, X-Requested-With, Content-Type, Accept"
        # response['Access-Control-Allow-Credentials']="true"
        # response['Access-Control-Allow-Headers'] = "xxx"
        return response

    def get(self, request, *args, **kwargs):
        res_dic = {'code': 1000, 'msg': None}
        pk=kwargs['pk']
        course_obj= Course.objects.filter(pk=pk).first()
        ser = CourseSerialize(instance=course_obj, many=False)
        res_dic['course'] = ser.data
        res = HttpResponse(json.dumps(res_dic))
        res['Access-Control-Allow-Origin'] = "http://127.0.0.1:8080"
        res['Access-Control-Allow-Methods'] = "PUT,GET,POST"
        res['Access-Control-Allow-Headers'] = "Authorization,Origin, X-Requested-With, Content-Type, Accept"
        return res


class CourseListView(APIView):
    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = "http://127.0.0.1:8080"
        response['Access-Control-Allow-Methods'] = "PUT,GET,POST"
        response['Access-Control-Allow-Headers'] = "Authorization,Origin, X-Requested-With, Content-Type, Accept"
        # response['Access-Control-Allow-Credentials']="true"
        # response['Access-Control-Allow-Headers'] = "xxx"
        return response
    def get(self,request,*args,**kwargs):
        res_dic = {'code': 1000, 'msg': None}
        course_list = Course.objects.all()
        ser = CourseSerialize(instance=course_list,many=True)
        res_dic['course_list'] =ser.data
        res=HttpResponse(json.dumps(res_dic))
        res['Access-Control-Allow-Origin'] = "http://127.0.0.1:8080"
        res['Access-Control-Allow-Headers'] = "Authorization,Origin, X-Requested-With, Content-Type, Accept"
        return res

