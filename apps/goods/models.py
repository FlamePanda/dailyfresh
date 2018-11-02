from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField
# Create your models here.

class GoodsType(BaseModel):
	'''商品类型模型类'''
	name = models.CharField(max_length=20,verbose_name='种类名称')
	logo = models.CharField(max_length=20,verbose_name='标识')
	image = models.ImageField(upload_to='type',verbose_name='商品类型图片')
	
	class Meta:
		db_table = 'df_goods_type'
		verbose_name = '商品种类'
		verbose_name_plural = verbose_name
		
	def __str__(self):
		return self.name

class GoodsSKU(BaseModel):
	'''商品SKU模型类'''
	status_choices = (
		(0,'下线'),
		(1,'上线'),
)
	goods_type = models.ForeignKey('GoodsType',verbose_name='商品种类',db_column='type',on_delete=models.CASCADE) 
	goods = models.ForeignKey('Goods',verbose_name='商品SPU',on_delete=models.CASCADE)
	name = models.CharField(max_length=20,verbose_name='商品名称')
	desc = models.CharField(max_length=256,verbose_name='商品简述')
	price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品价格')
	unite = models.CharField(max_length=20,verbose_name='商品单位')
	image = models.ImageField(upload_to='goods',verbose_name='商品图片')
	store = models.IntegerField(default=1,verbose_name='商品库存')
	sales = models.IntegerField(default=0,verbose_name='商品销量')
	status = models.SmallIntegerField(default=1,choices=status_choices,verbose_name='是否上线')
	class Meta:
		db_table = 'df_goods_sku'
		verbose_name = '商品'
		verbose_name_plural = verbose_name

class Goods(BaseModel):
	'''商品SPU类'''
	name = models.CharField(max_length=20,verbose_name='商品SPU你名称')
	# 富文本编辑框
	detail = HTMLField(blank=True,verbose_name='商品详情')
	
	class Meta:
		db_table = 'df_goods'
		verbose_name = '商品SPU'
		verbose_name_plural = verbose_name

class GoodsImage(BaseModel):
	'''商品图片模型类'''
	sku = models.ForeignKey('GoodsSKU',verbose_name='商品',on_delete=models.CASCADE)
	image = models.ImageField(upload_to='goods',verbose_name='图片路径')
	
	class Meta:
		db_table = 'df_goods_image'
		verbose_name = '商品图片'
		verbose_name_plural = verbose_name


class IndexGoodsBanner(BaseModel):
	'''首页图片轮播模型类'''
	sku = models.ForeignKey('GoodsSKU',verbose_name='商品',on_delete=models.CASCADE)
	image = models.ImageField(upload_to='banner',verbose_name='图片')
	index = models.SmallIntegerField(default=0,verbose_name='展示顺序')
	
	class Meta:
		db_table = 'df_index_banner'
		verbose_name = '首页轮播商品'
		verbose_name_plural = verbose_name

class IndexTypeGoodsBanner(BaseModel):
	'''首页分类商品展示类'''
	display_choices = (
		(0,'标题'),
		(1,'图片'),
)
	
	goods_type = models.ForeignKey('GoodsType',verbose_name='商品类型',on_delete=models.CASCADE)
	sku = models.ForeignKey('GoodsSKU',verbose_name='商品SKU',on_delete=models.CASCADE)
	disply_type = models.SmallIntegerField(default=1,choices=display_choices,verbose_name='展示类型')
	index = models.SmallIntegerField(default=0,verbose_name='展示顺序')
	
	class Meta:
		db_table = 'df_index_type_goods'
		verbose_name = '主页分类商品展示'
		verbose_name_plural = verbose_name

class IndexPromotionBanner(BaseModel):
	'''首页促销商品展示模型类'''
	name = models.CharField(max_length=20,verbose_name='活动名称')
	url = models.URLField(verbose_name='活动链接')
	image = models.ImageField(upload_to='banner',verbose_name='活动图片')
	index = models.SmallIntegerField(default=0,verbose_name='展示顺序')
	
	class Meta:
		db_table = 'df_index_promotion'
		verbose_name = '主页促销活动'
		verbose_name_plural = verbose_name

