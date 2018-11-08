from django.urls import path
from goods.views import IndexView,DetailView,ListView

urlpatterns = [
	path('index',IndexView.as_view(),name='index'), # 首页
	path('goods/<int:goods_id>',DetailView.as_view(),name='detail'), # 商品详情页
	path('list/<int:type_id>/<int:page_index>',ListView.as_view(),name='list'), # 商品list表页
]
