from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.

# /cart/add （sku_id,count）
class AddView(View):
	'''添加商品到用户购物车'''
	def post(self,request):
		# 业务处理
		# 判断用户是否登录
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res':0,'errmsg':'请先登录！'})
		# 获取数据
		sku_id = request.POST.get('sku_id')
		count = request.POST.get('count')
		# 校验数据 
		if not all([sku_id,count]):
			return JsonResponse({'res':1,'errmsg':'数据错误！'})

		try:
			count = int(count)
		except Exception as ex:
			return JsonResponse({'res':5,'errmsg':'数据错误！'})

		try:
			sku = GoodsSKU.objects.get(id=sku_id)
		except GoodsSKU.DoesNotExist as ex:
			return JsonResponse({'res':2,'errmsg':'不存在该商品！'})
		# 数据库添加
		conn = get_redis_connection('default')
		cart_key = 'cart_%d'%user.id
		preivous_count = conn.hget(cart_key,sku.id)
		if preivous_count:
			count = count + int(preivous_count)
		# 如果商品的库存不足
		if count > sku.store:
			return JsonResponse({'res':3,'errmsg':'库存不足！'})
		conn.hset(cart_key,sku.id,count)
		# 查询数据库原有的商品种类数量
		count = conn.hlen(cart_key)
		return JsonResponse({'res':4,'msg':'添加成功！','count':count})


# /cart
class CartView(LoginRequiredMixin,View):
	'''购物车主页面'''
	def get(self,request):
		# 业务处理
		# 获取当前用户
		user = request.user
		# 查询数据库得到用户的购物车商品数量
		conn = get_redis_connection('default') # 得到连接
		cart_key = 'cart_%d'%(user.id) # 得到用户购物车存储的键
		skus_dict = conn.hgetall(cart_key) # 得到用户购物商品的集合
		# 定义用户商品的列表，商品的总件数，总金额。
		skus = []
		total_count = 0
		total_amount = 0
		for sku_id,count in skus_dict.items(): # 遍历集合，得到商品的id和数量
			# 得到商品sku
			sku = GoodsSKU.objects.get(id=int(sku_id))
			# 计算商品的小计
			amount = sku.price * int(count)
			# 动态的添加count和amount
			sku.count = int(count)
			sku.amount = amount
            # 添加商品进入列表
			skus.append(sku)
			# 累计商品的总件数和总金额
			total_count = int(count) + total_count
			total_amount = amount + total_amount
		# 组织上下文
		context = {'skus':skus,
					'total_count':total_count,
					'total_amount':total_amount
				}
		# 返回应答
		return render(request,'cart/cart.html',context)

# /cart/update
class UpdateView(View):
	'''修改用户商品的数量'''
	def post(self,request):
		# 判断用户是否登录
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res':0,'errmsg':'请先登录！'})
		# 获取数据
		sku_id = request.POST.get('sku_id')
		count = request.POST.get('count')
		# 校验数据 
		if not all([sku_id,count]):
			return JsonResponse({'res':1,'errmsg':'数据错误！'})

		try:
			count = int(count)
		except Exception as ex:
			return JsonResponse({'res':5,'errmsg':'数据错误！'})

		try:
			sku = GoodsSKU.objects.get(id=sku_id)
		except GoodsSKU.DoesNotExist as ex:
			return JsonResponse({'res':2,'errmsg':'不存在该商品！'})
		# 数据库添加
		conn = get_redis_connection('default')
		cart_key = 'cart_%d'%user.id
		# 如果商品的库存不足
		if count > sku.store:
			return JsonResponse({'res':3,'errmsg':'库存不足！'})
		conn.hset(cart_key,sku.id,count)
		# 查询数据库用户的商品数量
		count = sum([int(x) for x in conn.hvals(cart_key)])
		return JsonResponse({'res':4,'msg':'添加成功！','count':count})


# /cart/delete
class DeleteView(View):
	'''删除用户对应商品'''
	def post(self,request):
		# 判断用户是否登录
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res':0,'errmsg':'请先登录！'})
		# 获取数据
		sku_id = request.POST.get('sku_id')
		# 校验数据 
		if not all([sku_id]):
			return JsonResponse({'res':1,'errmsg':'数据错误！'})

		try:
			sku = GoodsSKU.objects.get(id=sku_id)
		except GoodsSKU.DoesNotExist as ex:
			return JsonResponse({'res':2,'errmsg':'不存在该商品！'})
		# 业务处理，数据库删除
		conn = get_redis_connection('default')
		cart_key = 'cart_%d'%user.id
		conn.hdel(cart_key,sku.id)
		# 查询数据库用户的商品数量
		count = sum([int(x) for x in conn.hvals(cart_key)])
		return JsonResponse({'res':4,'msg':'删除成功！','count':count})

