from django.conf.urls import url,include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'api/(?P<verstion>[v1|v2]+)/',include('app01.urls')),
]
