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

class CorsMiddleware(MiddlewareMixin):
    def process_response(self,request,response):
        response['Access-Control-Allow-Origin'] = "*"
        response['Access-Control-Allow-Headers'] = "true"
        response['Access-Control-Allow-Headers'] = "Content-Type"
        return response

