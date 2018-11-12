from django.shortcuts import render,redirect
from django.views.generic import View
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from goods.models import GoodsSKU 
from user.models import Address
from django_redis import get_redis_connection
from django.http import JsonResponse
from order.models import OrderInfo,OrderGoods
import datetime
from django.db import transaction
from utils.alipay import Alipay
# Create your views here.

class PlaceOrderView(LoginRequiredMixin,View):
	'''订单准备页'''
	def post(self,request):
		# 获取数据
		user = request.user
		skus_id = request.POST.getlist('sku_id')
		# 校验数据
		if not all(skus_id): # 如果没有商品，返回购物车页面。
			return redirect(reverse('cart:center'))
		# 遍历所有的商品
		total_count = 0 # 商品的总数量
		total_price = 0 # 商品的总价格		
		skus = [] # 所有的商品
		for sku_id in skus_id:
			try:
				# 获取商品 
				sku = GoodsSKU.objects.get(id=sku_id)
			except GoodsSKU.DoesNotExist as ex:
				return redirect(reverse('cart:center'))
			# 从数据库中取出商品的数量
			conn = get_redis_connection('default')
			cart_key = 'cart_%d'%user.id
			count = int(conn.hget(cart_key,sku.id))
			# 计算商品的小计
			aomunt = sku.price * count
			# 动态的给商品添加属性，小计和数量
			sku.count = count
			sku.aomunt = aomunt
			# 追加商品
			skus.append(sku)
			# 累加所有的商品价格和数量
			total_price += aomunt
			total_count += count
		# 得到用户的所有地址
		addrs = Address.objects.filter(user=user)
		# 得到运费（有专门一个子系统用来生成运费单）
		transport = 10
		# 实际付款
		final_price = total_price+transport
		# 组织上下文
		context = {'skus':skus,
					'addrs':addrs,
					'transport':transport,
					'total_count':total_count,
					'total_price':total_price,
					'final_price':final_price
					}
		# 返回应答
		return render(request,'order/place_order.html',context)

# /order/commit
class CommitView(View):
	'''订单处理类'''
	
	@transaction.atomic
	def post(self,request):
		# 用户身份认证
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res':0,'errmsg':'请先登录！'})
		# 获取数据
		addr_id = request.POST.get('addr_id')
		pay_style = request.POST.get('pay_style')
		skus_id = request.POST.get('skus_id').split(',')
		# 校验数据
		if not all([addr_id,pay_style,skus_id]): # 校验所有数据不能为空。
			return JsonResponse({'res':1,'errmsg':'数据有误！'})
		try:
			# 校验地址正确
			addr = Address.objects.get(id=addr_id,user=user)
		except Address.DoesNotExist as ex:
			return JsonResponse({'res':3,'errmsg':'地址信息错误！'})
		if pay_style not in OrderInfo.PAY_TYPE_CHOICES.keys(): # 校验支付方式是否合法
			return JsonResponse({'res':5,'errmsg':'支付方式非法！'})
		# 业务处理
		# 订单ID
		order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")+str(user.id) 
		# 订单的总数量和总价格
		total_count = 0
		total_price = 0
		# 订单的运费
		transport_price = 10
		# 创建保存点
		save_id = transaction.savepoint()
		try:
			# 生成订单
			order = OrderInfo.objects.create(order_id=order_id,user=user,addr=addr,pay_method=pay_style,total_count=total_count,total_price=total_price,transport_price=transport_price)
			# 遍历skus
			skus_id = [int(x) for x in skus_id]
			# 得到数据库的连接
			conn = get_redis_connection('default')
			for sku_id in skus_id:
				try:
					print(sku_id)
					sku = GoodsSKU.objects.select_for_update().get(pk=sku_id)
				except Exception as ex:
					transaction.savepoint_rollback(save_id)
					return JsonResponse({'res':8,'errmsg':'商品不存在！'})
				cart_key = 'cart_%d'%user.id
				# 得到商品的数量
				count = int(conn.hget(cart_key,sku.id))
				# 判断商品的库存
				if count > sku.store:
					# 回滚
					transaction.savepoint_rollback(save_id)
					return JsonResponse({'res':6,'errmsg':'商品库存不足！'})
				# 向订单商品表中插入一条数据
				OrderGoods.objects.create(order=order,sku=sku,count=count,price=sku.price)
				# 减少商品的库存和增加商品的销量
				sku.store = sku.store - count 
				sku.sales = sku.sales + count
				sku.save()
				# 计算商品的总价格和总数量
				total_count += count
				total_price += count*sku.price
			# 更新订单
			order.total_count = total_count
			order.total_price = total_price
			order.save()
		except Exception as ex:
			# 回滚
			transaction.savepoint_rollback(save_id)
			return JsonResponse({'res':7,'errmsg':'下单失败！'})
		# 提交事务
		transaction.savepoint_commit(save_id)
		# 清空数据库对应的购物车数量
		conn.hdel(cart_key,*skus_id)
		# 返回应答
		return JsonResponse({'res':4,'msg':'succeed！'})
	
# /order/pay
class OrderPayView(View):
	'''订单支付页'''
	def post(self,request):
		# 用户校验
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res':0,'errmsg':'请先登录！'})
		# 订单校验
		order_id = request.POST.get('order_id')
		try:
			order = OrderInfo.objects.get(order_id=order_id,
											user=user,
											pay_method=3,
											order_status=1)
		except OrderInfo.DoesNotExist :
			return JsonResponse({'res':1,'errmsg':'订单异常'})
		# 业务处理
		total_amount = order.total_price + order.transport_price
		response_url = Alipay.get_pay_url(order.order_id,total_amount)
		# 返回应答
		return JsonResponse({'res':4,'url':response_url})

# /order/check
class OrderCheckView(View):
	'''支付查询'''
		
	def post(self,request):
		# 用户校验
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res':0,'errmsg':'请先登录！'})
		# 订单校验
		order_id = request.POST.get('order_id')
		try:
			order = OrderInfo.objects.get(order_id=order_id,
											user=user,
											pay_method=3,
											order_status=1)
		except OrderInfo.DoesNotExist :
			return JsonResponse({'res':1,'errmsg':'订单不存在！'})
		# 业务处理，查询订单是否支付成功
		# 获取查询返回值
		result = Alipay.get_pay_status(order.order_id)
		# 如果为真
		if result:
			order.order_status = 4
			order.trade_no = result
			order.save()
		else:
			return JsonResponse({'res':2,'errmsg':'支付失败！'})
		# 返回应答
		return JsonResponse({'res':4,'msg':'succceed!'})
