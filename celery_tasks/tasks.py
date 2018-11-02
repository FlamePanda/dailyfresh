from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

#import os
#import django
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
#django.setup()


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

