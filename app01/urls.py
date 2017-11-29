from django.conf.urls import url
from app01 import views

urlpatterns = [
    url(r'^login/',views.AuthView.as_view()),
    url(r'^index/',views.IndexView.as_view()),
    url(r'^course/',views.CourseDetailView.as_view()),
    url(r'^course/(?P<course_id>\d+)',views.CourseDetailView.as_view()),
    url(r'^course_list/',views.CourseListView.as_view()),
]
