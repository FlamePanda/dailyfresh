from django.urls import path
from user.views import RegisterView,ActiveView,LoginView,AddressView,OrderView,CenterView,LogoutView

urlpatterns = [
		path('register',RegisterView.as_view(),name='register'), # 用户注册
		path('active/<str:token>',ActiveView.as_view(),name='active'), # 用户激活
		path('login',LoginView.as_view(),name='login'), # 用户登录
		path('logout',LogoutView.as_view(),name='logout'), # 用户退出


		path('address',AddressView.as_view(),name='address'), # 用户地址
		path('order',OrderView.as_view(),name='order'), # 用户订单
		path('',CenterView.as_view(),name='center'), # 用户中心
]
