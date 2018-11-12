from django.shortcuts import render,redirect
from django.urls import reverse
from django.views.generic import View
from re import match
from user.models import User,Address
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer ,BadSignature,SignatureExpired
from django.conf import settings
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from order.models import OrderInfo,OrderGoods
from django.core.paginator import Paginator
# Create your views here.


# /user/register 
class RegisterView(View):
	'''通用视图类，用于处理注册请求'''
	
	def get(self,request):
		'''处理GET请求'''
		return render(request,'user/register.html')
	
	def post(self,request):
		'''处理表单请求'''
		# 获取用户数据
		user_name = request.POST.get('user_name')
		password = request.POST.get('pwd')
		ensure_pwd = request.POST.get('cpwd')
		user_email = request.POST.get('email')
		allow = request.POST.get('allow') 
		# 校验用户数据
		if not all([user_name,user_email,password,ensure_pwd]):
			# 如果不满足，返回注册页面，并提示所有表格不能为空
			return render(request,'user/register.html',{'errmsg':'所有表格不能为空！'})
		if password != ensure_pwd:
			# 如果不满足，返回注册页面，并提示密码不一致
			return render(request,'user/register.html',{'errmsg':'密码不一致！'})
		if not match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',user_email):
			# 如果不满足，返回注册页面，并提示邮箱格式不正确
			return render(request,'user/register.html',{'errmsg':'邮箱格式不正确！'})
		if allow != 'on':
			# 如果不满足，返回注册页面，并提示请同意该协议
			return render(request,'user/register.html',{'errmsg':'请同意该协议！'})
		if User.objects.filter(username=user_name):
			# 如果满足，返回注册页面，并提示该用户已经注册
			return render(request,'user/register.html',{'errmsg':'该用户已经注册！'})
		# 注册该用户
		user = User.objects.create_user(user_name,user_email,password)
		user.is_active = 0 # 该用户未激活
		user.save()
		# 发送注册邮件
		serializer = Serializer(settings.SECRET_KEY,3600) # 创建一个加密对象
		info = {'user_id':user.id} # 加密数据
		token = serializer.dumps(info).decode()
		# 发送
		send_register_active_email.delay(user_email,user_name,token)
		# 返回主页
		return redirect(reverse('goods:index'))

# /user/active
class ActiveView(View):
	'''处理用户激活类'''
	def get(self,request,token):
		'''对token进行解析，进行用户激活'''
		serializer = Serializer(settings.SECRET_KEY,3600) # 创建一个加密对象
		try:
			# 获取对应数据包的信息
			info = serializer.loads(token)
			# 得到用户实例对象
			user_id = info['user_id']
			# 用户激活
			user = User.objects.get(id=user_id)
			user.is_active = 1
			user.save()
			# 重定向至登录页
			return redirect(reverse('user:login'))
		except BadSignature as bs:
			# 篡改数据包
			return HttpResponse('链接已失效！')
		except SignatureExpired as se:
			# 数据包已过期
			return HttpResponse('链接已过期！')
		except Exception as ex:
			# 内部错误
			return HttpResponse('内部错误！')

# user/login
class LoginView(View):
	'''用户登录视图类'''
	def get(self,request):
		# 返回登录页面
		if 'user_name' in request.COOKIES:
			user_name = request.COOKIES.get('user_name')
			checked = 'checked'
		else:
			user_name = ''
			checked = ''
		return render(request,'user/login.html',{'user_name':user_name,'checked':checked})
	
	def post(self,request):
		'''处理用户登陆验证'''
		# 获取用户数据
		user_name = request.POST.get('username')
		password = request.POST.get('pwd')
		remember = request.POST.get('remember')
		# 校验用户数据
		if not all([user_name,password]):
				return render(request,'user/login.html',{'errmsg':'用户信息不完整！'})
		user = authenticate(username=user_name, password=password)
		# 业务处理，检查用户是否合法
		if user is not None:
			# 用户有效
			if user.is_active:
				# 用户已激活
				# 记住用户ID
				login(request,user)
				# 判断用户是否要进入next所对应的URL中。
				response = redirect(request.GET.get('next',reverse('goods:index')))
				# 查看用户是否勾选记住用户名
				if remember == 'on':
					# 记住用户名
					response.set_cookie('user_name',user_name,max_age=14*24*3600)	
				else:
					# 删除用户名
					response.delete_cookie('user_name')
				# 返回响应
				return response
			else:
				# 用户未激活
				return render(request,'user/login.html',{'errmsg':'请激活账户！'})
		else:
			# 用户不存在
			return render(request,'user/login.html',{'errmsg':'用户名或密码错误！'})

# /user/logout
class LogoutView(View):
	'''用户登出视图类'''
	
	def get(self,request):
		# 清除用户数据
		logout(request)
		# 重定向至首页
		return redirect(reverse('goods:index'))


# /user
class CenterView(LoginRequiredMixin,View):
	'''用户中心视图类'''
	
	def get(self,request):
		'''返回用户中心视图'''
		# 业务处理，获取用户的地址和用户信息
		address = Address.objects.get_default_address(request.user)
		# 业务处理，获取用户的最近浏览
		# 得到Redis数据库的连接
		con = get_redis_connection('default')
		# 得到Redis数据库的key
		history_key = 'history_%d'%(request.user.id)
		# 如果存在对应的键
		goods_list = []
		if con.exists(history_key):
			# 得到goods的skus_id
			skus_id = con.lrange(history_key,0,4)
			skus_id = [int(sku_id.decode()) for sku_id in skus_id]
			# 依照顺序得到对应的goods信息
			skus = GoodsSKU.objects.filter(id__in=skus_id)
			for sku_id in skus_id:
				for sku in skus:
					if sku_id == sku.id:
						goods_list.append(sku)
		# 上下文
		context = {'page':'info','address':address,'goods_list':goods_list}
		# 返回
		return render(request,'user/user_center_info.html',context)


# /user/order/page
class OrderView(LoginRequiredMixin,View):
	'''用户订单视图类'''
	
	def get(self,request,page_index):
		user = request.user
		# 获取所有的订单
		orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
		# 获取所有的订单商品
		for order in orders:
			# 获取每个订单对应的订单商品
			order_skus = OrderGoods.objects.filter(order=order)
			# 得到每个商品的小计
			for order_sku in order_skus:
				amount = order_sku.count * order_sku.price
				# 动态的给每个商品添加小计
				order_sku.amount = amount 
			# 动态的给订单添加订单商品
			order.order_skus = order_skus
			# 动态的给订单添加订单状态
			order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.order_status]
		# 分页
		paginator = Paginator(orders,2)
		# 对页码进行容错处理
		pages = paginator.get_page(page_index)
		# 自定义分页显示
		# 只显示五页，①当<5时,显示所有页面，②当大于5时，以其为中心，③末尾事显示后五页
		if paginator.num_pages < 5:
			pages.index = range(1,paginator.num_pages+1)
		elif paginator.num_pages >= pages.number + 2 and pages.number < 3:
			pages.index = range(1,6) 
		elif paginator.num_pages >= pages.number + 2 and pages.number - 2 >= 1:
			pages.index = range(pages.number-2,pages.number+3)
		else:
			page.index = range(paginator.num_pages-4,paginator.num_pages+1)
		# 组织上下文
		context = {'pages':pages,'page':'order'}
		return render(request,'user/user_center_order.html',context)

	def post(self,request):
		'''处理用户订单请求'''
		pass

# /user/address
class AddressView(LoginRequiredMixin,View):
	'''用户地址视图类'''
	
	def get(self,request):
		# 业务处理： 获取用户的默认地址
		address = Address.objects.get_default_address(request.user)
		# 返回页面
		return render(request,'user/user_center_site.html',{'page':'address','address':address})
	
	def post(self,request):
		'''处理用户地址请求'''
		# 接收用户提交的数据
		receiver = request.POST.get('receiver')
		detail_address = request.POST.get('detail_address')
		postcode = request.POST.get('postcode')
		phone = request.POST.get('phone')
		# 校验数据合法性
		if not all([receiver,detail_address,phone]):
			return render(request,'user/user_center_site.html',{'errmsg':'内容不允许为空！'})
		if not match(r'^(13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-9]|19[89])\d{8}$',phone):
			return render(request,'user/user_center_site.html',{'errmsg':'手机号错误！'})
		# 业务处理，添加地址进数据库
		# 查看用户地址是否含有默认地址
		user = request.user
		address = Address.objects.get_default_address(user)
		if address:
			is_default = False
		else:
			is_default = True
		print('address:',address)
		print('is_default:',is_default)
		Address.objects.create(user=user,receiver=receiver,addr=detail_address,zip_code=postcode,phone=phone,is_default=is_default)
		# 刷新页面
		return redirect(reverse('user:address'))
