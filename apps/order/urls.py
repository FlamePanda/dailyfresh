from django.urls import path
from order.views import PlaceOrderView,CommitView,OrderPayView,OrderCheckView 

urlpatterns = [
	path('place_order',PlaceOrderView.as_view(),name='place_order'),# 订单准备页
	path('commit',CommitView.as_view(),name='commit'),# 订单提交页
	path('pay',OrderPayView.as_view(),name='pay'),# 订单支付页
	path('check',OrderCheckView.as_view(),name='check'),# 订单支付校验页
]
