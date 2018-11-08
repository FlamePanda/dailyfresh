from django.shortcuts import render,redirect
from goods.models import Goods,GoodsType,GoodsSKU,GoodsImage,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from django.urls import reverse
from order.models import OrderGoods
from django.core.paginator import Paginator
# Create your views here.

# /index
class IndexView(View):
	'''首页视图类'''
	def get(self,request):
		# 判断是否缓存
		context = cache.get('index_page_data')
		if context is None:
			# 业务处理
			context = {}
			# 获取所有的轮播商品
			index_goods_banners = IndexGoodsBanner.objects.all().order_by('index')
			context['index_goods_banners'] = index_goods_banners
			# 获取所有的促销商品
			index_promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
			context['index_promotion_banners'] = index_promotion_banners
			# 获取所有的商品种类
			goods_types = GoodsType.objects.all()
			context['goods_types'] = goods_types
			# 遍历所有的商品种类
			for goods_type in goods_types:
				# 获取所有的图片类型的展示商品
				graph_goods = IndexTypeGoodsBanner.objects.filter(goods_type=goods_type).filter(disply_type=1).order_by('index')[:4]
				# 获取所有的文字类型的展示商品
				text_goods = IndexTypeGoodsBanner.objects.filter(goods_type=goods_type).filter(disply_type=0).order_by('index')[:4]
				# 动态的给goods_type 添加属性，graph_goods和text_goods
				goods_type.graph_goods = graph_goods
				goods_type.text_goods = text_goods
				# 添加context缓存,过期时间一个小时
				cache.set('index_page_data',context,3600)
	
		# 获取用户购物车中的记录
		user = request.user
		cart_count = 0
		if user.is_authenticated:
			# 如果用户已登录
			# 得到Redis数据库的连接
			client = get_redis_connection('default')
			# 得到用户数据库的键
			cart_key = 'cart_%d'%user.id
			# 得到用户购物车的商品的数量
			cart_count = client.hlen(cart_key)
		context['cart_count'] = cart_count
		# 返回模板HTML
		return render(request,'goods/index.html',context)

# /goods/goods_id
class DetailView(View):
	'''商品详情页'''
	
	def get(self,request,goods_id):
		'''获取商品的信息信息'''
		# 业务处理
		# 商品的详情
		try:
			sku = GoodsSKU.objects.get(id=goods_id)
		except Exception as ex:
			# 说明无此商品，重定向至首页
			return redirect(reverse('goods:index'))
		# 所有商品类型
		types = GoodsType.objects.all()	
		# 同SKU的商品
		skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku.id)
		# 商品的评论
		order_comments = OrderGoods.objects.filter(sku=sku).exclude(comment='')
		# 新品推荐
		new_goods = GoodsSKU.objects.filter(goods_type=sku.goods_type).exclude(id=sku.id).order_by('-create_time')[:2]
		# 购物车数量
		# 获取用户购物车中的记录
		user = request.user
		cart_count = 0
		if user.is_authenticated:
			# 如果用户已登录
			# 得到Redis数据库的连接
			client = get_redis_connection('default')
			# 得到用户数据库的键
			cart_key = 'cart_%d'%user.id
			# 得到用户购物车的商品的数量
			cart_count = client.hlen(cart_key)
			
			# 添加用户最近浏览
			# 用户历史记录的键
			history_key = 'history_%d'%user.id
			# 删除存在的值
			client.lrem(history_key,0,sku.id)
			# 插入最新的值
			client.lpush(history_key,sku.id)
			# 保留最近的5条记录
			client.ltrim(history_key,0,5)
		# 上下文
		context = {'sku':sku,
					'types':types,
					'skus':skus,
					'order_comments':order_comments,
					'new_goods':new_goods,
					'cart_count':cart_count}
		return render(request,'goods/detail.html',context)

# list/type_id/page_index?sort='default','price','hot'
class ListView(View):
	'''商品类别的所有商品列表显示'''
	
	def get(self,request,type_id,page_index):
		# 业务处理
		# 验证type_id是否存在
		try:
			goods_type = GoodsType.objects.get(id=type_id)
		except Exception as ex:
			return redirect(reverse('goods:index'))	
		# 获取所有的类型
		types = GoodsType.objects.all()	
		# 获取该种类的所有商品
		sort = request.GET.get('sort')
		# 按照一定规则进行排序
		if sort == 'price':
			skus = GoodsSKU.objects.filter(goods_type=goods_type).order_by('price')
		elif sort == 'hot':
			skus = GoodsSKU.objects.filter(goods_type=goods_type).order_by('-sales')
		else:
			sort = 'default'
			skus = GoodsSKU.objects.filter(goods_type=goods_type).order_by('id')
		# 分页显示
		paginator = Paginator(skus,2)
		# 对页码进行容错处理
		page = paginator.get_page(page_index)
		# 自定义分页显示
		# 只显示五页，①当<5时,显示所有页面，②当大于5时，以其为中心，③末尾事显示后五页
		if paginator.num_pages < 5:
			page.index = range(1,paginator.num_pages+1)
		elif paginator.num_pages >= page.number + 2 and page.number < 3:
			page.index = range(1,6) 
		elif paginator.num_pages >= page.number + 2 and page.number - 2 >= 1:
			page.index = range(page.number-2,page.number+3)
		else:
			page.index = range(paginator.num_pages-4,paginator.num_pages+1)
		# 获取新品推荐
		new_goods = GoodsSKU.objects.filter(goods_type=goods_type).order_by('-create_time')[:2]
		# 获取用户购物车中的记录
		user = request.user
		cart_count = 0
		if user.is_authenticated:
			# 如果用户已登录
			# 得到Redis数据库的连接
			client = get_redis_connection('default')
			# 得到用户数据库的键
			cart_key = 'cart_%d'%user.id
			# 得到用户购物车的商品的数量
			cart_count = client.hlen(cart_key)
		# 组织模板上下文
		context = {'goods_type':goods_type,
					'types':types,
					'sort':sort,
					'page':page,
					'cart_count':cart_count,
					'new_goods':new_goods}
						
		return render(request,'goods/list.html',context)
