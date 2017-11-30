from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,redirect
from rest_framework.views import APIView
from app01.models import Account, Token, Course, CourseDetail,Order,OrderDetail,PricePolicy,CouponRecord
from app01.utils.auth import LuffyAuthentication
from app01.utils.commons import gen_token
from django.core import serializers
from app01.utils.throttle import LuffyAnonRateThrottle, LuffyUserRateThrottle
from rest_framework import serializers
from rest_framework.response import Response
from app01.utils.pay import alipay
from django.db.models import F
from app01.utils.permission import LuffyPermission
import json
from urllib.parse import parse_qs
import time
import re

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

class CreateOrder(APIView):
    '''
    支付订单视图
    '''
    def create_order(self,payment_method,order_number,account,actual_amount,payment_number=None,):
        '''
        创建订单
        :param payment_method: 付款方式
        :param order_number: 订单号
        :param account: 用户
        :param actual_amount: 实际金额
        :param payment_number: 支付宝流水
        :return:
        '''
        payment_type = {'微信':0,'支付宝':1,'优惠码':2,'贝里':3}
        py_type = payment_type[payment_method]
        obj = Order.objects.create(payment_type=py_type,
                                   order_number=order_number,
                                   account=account,
                                   status=1,
                                   actual_amount=actual_amount
                                   )

        return obj

    def get_valid_time(self,valid_period):
        '''

        :param create_time: 现在的时间
        :param valid_period: 该课程的有效期
        :return: 有效期至
        '''
        # h = create_time.replace(' ', '')
        # m = create_time[:10]
        # n = create_time[10:]
        # x_time = m + ' ' + n
        # format_time = time.strptime(x_time, "%Y-%m-%d %H:%M:%S")
        # stamp_time = time.mktime(format_time)

        stamp_time = time.time()
        valid_period_display = stamp_time + valid_period*24*60*60
        return valid_period_display

    def create_detail_order(self,courses,order,discount):
        '''
        创建订单详细
        :param courses: 课程列表
        :param order: 订单号
        :param discount: 折扣 
        :return:
        '''
        for course in courses:
            course_obj = Course.objects.filter(id=course.get('course_id')).first()
            price = PricePolicy.objects.filter(id=course.get('price_id')).first()
            valid_period =  price.get_valid_period_display()
            valid_num = re.findall('(\d+)',valid_period)
            valid_num = int(valid_num[0])
            OrderDetail.objects.create(order=order,
                                       content_object=course_obj,
                                       original_price=price.price,
                                       price = price.price*discount,
                                       valid_period_display= self.get_valid_time(valid_period=price.valid_period),
                                       valid_period = valid_num,
                                       )

    def coupon_valid(self, coupon_record_obj):
        '''
        判断优惠券时间是否有效
        :param coupon_record_obj: 优惠券领取记录对象
        :return: True／False
        '''
        c = time.time()
        open_date = coupon_record_obj.coupon.valid_begin_date
        close_date = coupon_record_obj.coupon.valid_end_date
        open_date = str(open_date)
        x = time.strptime(open_date, '%Y-%m-%d')
        y = time.mktime(x)
        close_date = str(close_date)
        a = time.strptime(close_date, '%Y-%m-%d')
        b = time.mktime(a)

        if y < c < b:
            return True
        return False

    def post(self, request, *args, **kwargs):
        ret = {'code': 1000, 'msg': '', 'error': []}
        # try:
        courses = request.data.get('courses')
        courses =eval(courses)
        coupon = request.data.get('coupons')
        coupon = CouponRecord.objects.filter(id=coupon,account=2,status=0,coupon__coupon_type=0).first()
        beili = request.data.get('beili')
        amount = request.data.get('amount')
        user_obj = Account.objects.filter(id=2).first()
        flag = True
        try:
            if beili and user_obj.balance == int(beili):
                flag = True
            else:
                flag = False
                ret['error'].append('账户余额信息不匹配')

            price_list = [] #折扣价
            origin_price_list = [] #原价
            for course in courses:
                course_id = course.get('course_id')
                price_id = course.get('price_id')
                coupon_id = course.get('coupons_id')
                price = PricePolicy.objects.filter(id=price_id).first()
                origin_price_list.append(price.price)
                if coupon_id:
                    coupon_obj = CouponRecord.objects.filter(id=coupon_id,account=2,status=0).first()
                    if not coupon_obj:
                        flag = False
                        ret['error'].append('您没有该优惠券')
                    else:
                        if not self.coupon_valid(coupon_obj):
                            flag = False
                            ret['error'].append('您的优惠券已过期')
                        coupon_type = coupon_obj.coupon.coupon_type
                        if coupon_type == 1:
                            '满100减50'
                            total_money = coupon_obj.coupon.minimum_consume
                            reduce_money = coupon_obj.coupon.money_equivalent_value
                            if price.price >= total_money:
                                course_price = price.price - reduce_money
                            else:
                                course_price = price.price
                            price_list.append(course_price)
                        elif coupon_type == 2:
                            '7折'
                            dis_count = coupon_obj.coupon.off_percent
                            course_price = price.price*(dis_count/100)
                            price_list.append(course_price)
                        else:
                            flag = False
                            ret['error'].append('优惠券错误')
                else:
                    price_list.append(price.price)
                course_obj = Course.objects.filter(id=course_id,status=0).first()
                if not course_obj:
                    flag = False
                    ret['error'].append('课程信息错误')
            discount_amount = 0
            for i in price_list:
                discount_amount += i
            origin_amount = 0
            for i in origin_price_list:
                origin_amount += i
            if coupon:
                if not self.coupon_valid(coupon):
                    flag = False
                    ret['error'].append('通用优惠券已过期')
                else:
                    dis_count = coupon.coupon.off_percent
                    total_money = coupon.coupon.minimum_consume
                    coupon.update(status=1)
                    if total_money:
                        '满100减50'
                        reduce_money = coupon.coupon.money_equivalent_value
                        if discount_amount >= total_money:
                            discount_amount = discount_amount  - reduce_money
                        else:
                            discount_amount = discount_amount
                    elif dis_count:
                        '7折'
                        dis_count = coupon.coupon.off_percent
                        discount_amount = discount_amount * (dis_count/100)
                    else:
                        flag = False
                        ret['error'].append('优惠券错误')
            else:
                flag = False
                ret['error'].append('您没有该优惠券')
            if discount_amount != float(amount):
                flag = False
                ret['error'].append('价格判断错误')

            Account.objects.filter(id=2).update(balance=F('balance') - beili)

            if flag:
                out_trade_no = "x2" + str(time.time()),
                out_trade_no = out_trade_no[0]
                total_amount = float(amount)
                ali = alipay()
                query_params = ali.direct_pay(
                    subject='路飞商城',
                    out_trade_no=out_trade_no,
                    total_amount=total_amount
                )
                discount = discount_amount / origin_amount
                if beili:
                    beili = float(beili)
                    if beili >= total_amount:
                        order = self.create_order(payment_method='贝里',
                                                  order_number=out_trade_no,
                                                  account=user_obj,
                                                  actual_amount=total_amount)
                        self.create_detail_order(courses, order, discount)
                    else:

                        order1_no = out_trade_no + 'beili'
                        order1 = self.create_order(payment_method='贝里',
                                                   order_number=order1_no,
                                                   account=user_obj,
                                                   actual_amount=beili)
                        self.create_detail_order(courses, order1, discount)
                        order2_no = out_trade_no + 'alipay'
                        order2 = self.create_order(payment_method='支付宝',
                                                   order_number=order2_no,
                                                   account=user_obj,
                                                   actual_amount=total_amount - beili)
                        self.create_detail_order(courses, order2, discount)
                else:
                    order = self.create_order(payment_method='支付宝',
                                              order_number=out_trade_no,
                                              account=user_obj,
                                              actual_amount=total_amount)
                    self.create_detail_order(courses, order, discount)
                pay_url = "https://openapi.alipaydev.com/gateway.do?{}".format(query_params)
                return redirect(pay_url)
        except Exception as e:
            ret['error'].append('信息错误')

        print(ret)
        return HttpResponse(json.dumps(ret))

class VerifyOrder(APIView):
    '''支付验证功能'''
    def get(self,request,*args,**kwargs):

        ali = alipay()
        ret = {'code': 1000, 'msg': '', 'error': []}
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = ali.verify(params, sign)
        if status:
            ret['msg'] = '支付成功'
        else:
            ret['msg'] = '支付失败'
            ret['msg'].append('支付失败')
        return HttpResponse(json.dumps(ret))

    def post(self,request,*args,**kwargs):
        ali = alipay()
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for     k, v in post_data.items():
            post_dict[k] = v[0]
        sign = post_dict.pop('sign', None)
        status = ali.verify(post_dict, sign)
        out_trade_no = post_dict['out_trade_no']
        trade_no = post_dict['trade_no']
        gmt_payment = post_dict['gmt_payment']
        if status:
            order_list=Order.objects.filter(order_number=out_trade_no).update(status=0,payment_number=trade_no,pay_time=gmt_payment)
            beili = Order.objects.filter(order_number=out_trade_no,payment_type=3).first().actual_amount
        else:
            order_list = Order.objects.filter(order_number=out_trade_no).update(status=1, payment_number=trade_no,pay_time=gmt_payment)
        return HttpResponse('POST返回')















