from django.contrib import admin

# Register your models here.
from app01.models import Account, Token, Course,\
    CourseSubCategory, DegreeCourse, CourseCategory, \
    Teacher, CourseDetail,PricePolicy,Coupon,CourseChapter,\
    CourseReview,EnrolledCourse,OrderDetail,Order,OftenAskedQuestion


class AccountAdmin(admin.ModelAdmin):
    list_display = ("username","email","uid","mobile","qq","weixin","profession","city","signature","brief",
                    "openid","gender_choices","gender","degree_choices","degree","birthday","id_card","password",
                    "name","head_img","role_choices","memo","date_joined"
                    )

# class CourseAdmin(admin.ModelAdmin):
#     list_display = ("name","course_img","course_type_choices","course_type","degree_course",
#                     "brief","level_choices","level","period","order","attachment_path",
#                     "template_id","coupon","price_policy"
#                     )
admin.site.register(Account,AccountAdmin)
admin.site.register(Token)
admin.site.register(Teacher)
admin.site.register(CourseSubCategory)
admin.site.register(CourseCategory)
admin.site.register(DegreeCourse)
admin.site.register(CourseDetail)
admin.site.register(PricePolicy)
admin.site.register(Course)
admin.site.register(Coupon)
admin.site.register(CourseChapter)
admin.site.register(CourseReview)
admin.site.register(EnrolledCourse)
admin.site.register(OrderDetail)
admin.site.register(Order)
admin.site.register(OftenAskedQuestion)