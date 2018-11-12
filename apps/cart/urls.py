from django.urls import path
from cart.views import AddView,CartView,UpdateView,DeleteView


urlpatterns = [
		path('add',AddView.as_view(),name='add'),# 购物车的商品添加操作
		path('update',UpdateView.as_view(),name='update'),# 修改商品数量
		path('delete',DeleteView.as_view(),name='delete'),# 删除商品
		path('',CartView.as_view(),name='center'),# 购物车页面
]
