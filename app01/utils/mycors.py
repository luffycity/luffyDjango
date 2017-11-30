#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@version: 
@author: morgana
@license: Apache Licence 
@contact: vipmorgana@gmail.com
@site: 
@software: PyCharm
@file: cors.py
@time: 2017/11/27 上午10:16
"""
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import HttpResponse

class CorsMiddleware(MiddlewareMixin):

    def process_request(self,request):
        if request.method == 'OPTIONS':
            return HttpResponse()


    def process_response(self,request,response):
        response['Access-Control-Allow-Origin'] = "http://127.0.0.1:8080"
        response['Access-Control-Allow-Headers'] = "true"
        response['Access-Control-Allow-Headers'] = "Content-Type"
        return response

