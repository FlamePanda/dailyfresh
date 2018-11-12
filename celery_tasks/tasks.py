from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

#import os
#import django
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
#django.setup()

# 导入商品模型类中的模型
from apps.goods.models import Goods,GoodsType,GoodsSKU,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
from django.template import loader


# 创建一个celery的实例
app = Celery('celery_tasks.tasks',broker='redis://192.168.232.135:6379/8')

# 创建任务函数

@app.task
def send_register_active_email(to_email,user_name,token):
	'''用于处理用户成功注册后发送激活邮件'''
	subject = '天天生鲜欢迎信息！'
	message = ''
	sender = settings.EMAIL_FROM
	receiver = [to_email]
	html_message = '<h1 align="center">%s,欢迎您注册成为天天生鲜会员</h1>请点击下面的链接>激活您的账号<br /><a href="http://192.168.232.135:8000/user/active/%s">http://192.168.232.135:8000/user/active/%s</a>'%(user_name,token,token)
	send_mail(subject,message,sender,receiver,html_message=html_message)

@app.task
def generate_static_index_html():
	'''生成首页静态页面'''
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
	# 生成模板HTML
	res = loader.get_template('goods/static_index.html')
	# 模板渲染
	result_html = res.render(context)
	# 保存页面到static/index.html
	path = os.path.join(settings.BASE_DIR,'static/index.html')
	with open(path,'w') as f:
		f.write(result_html)
