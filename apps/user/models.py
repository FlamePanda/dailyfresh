from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser,BaseModel):
	'''用户模型类，继承自Django自带的抽象类和定制的基础类''' 
	
	class Meta:
		'''表名，显示名'''
		db_table = 'df_user'
		verbose_name = '用户'
		verbose_name_plural = verbose_name


class AddressManager(models.Manager):
	'''地址模型管理类'''
	
	def get_default_address(self,user):
		try:
			address = self.get(user=user,is_default=True)	
		except Exception as ex:
			address = None
		return address

class Address(BaseModel):
	'''用户地址信息类'''
	user = models.ForeignKey('User',verbose_name='所属账户',on_delete=models.CASCADE)
	receiver = models.CharField(max_length=20,verbose_name='收件人')
	addr = models.CharField(max_length=256,verbose_name='收件地址')
	zip_code = models.CharField(max_length=6,null=True,verbose_name='邮政编码')
	phone = models.CharField(max_length=11,verbose_name='联系电话')
	is_default = models.BooleanField(default=False,verbose_name='是否默认')

	objects = AddressManager()	
	class Meta:
		db_table = 'df_address'
		verbose_name = '地址'
		verbose_name_plural = verbose_name
