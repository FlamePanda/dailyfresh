from django.shortcuts import render,redirect
from django.urls import reverse
from django.views.generic import View
from re import match
from user.models import User,Address
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer ,BadSignature,SignatureExpired
from django.conf import settings
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login


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
				# 查看用户是否勾选记住用户名
				response = redirect(reverse('goods:index'))
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

