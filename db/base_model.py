from django.db import models


# 建立一个所有模型的基类
# 包含创建时间，修改时间，删除标记。
# 元属性为抽象类。
class BaseModel(models.Model):
	'''项目中所有的类的基类'''
	create_time = models.DateTimeField(auto_now_add=True,verbose_name='创建时间')
	update_time = models.DateTimeField(auto_now=True,verbose_name='修改时间')
	is_delete = models.BooleanField(default=False,verbose_name='删除标记')
	
	class Meta:
		abstract = True
