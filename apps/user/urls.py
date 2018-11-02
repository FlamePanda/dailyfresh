from django.urls import path
from user.views import RegisterView,ActiveView,LoginView

urlpatterns = [
		path('register',RegisterView.as_view(),name='register'), # 用户注册
		path('active/<str:token>',ActiveView.as_view(),name='active'), # 用户激活
		path('login',LoginView.as_view(),name='login'), # 用户登录
]
