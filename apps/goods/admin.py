from django.contrib import admin
from goods.models import Goods,GoodsType,GoodsSKU,GoodsImage,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
from celery_tasks.tasks import generate_static_index_html
from django.core.cache import cache

# Register your models here.
class BaseAdmin(admin.ModelAdmin):
	'''模型管理类的基类'''
	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		# 增加或修改对应的模型类数据后，重新生成新的首页静态页面
		generate_static_index_html.delay()
		# 重新缓存新的首页
		cache.delete('index_page_data')
	
	def delete_model(self,request, obj):
		super().delete_model(request,obj)
		# 删除对应的模型类数据后，重新生成新的首页静态页面
		generate_static_index_html.delay()
		# 重新缓存新的首页
		cache.delete('index_page_data')
		

class GoodsTypeAdmin(BaseAdmin):
	pass

class IndexGoodsBannerAdmin(BaseAdmin):
	pass

class IndexTypeGoodsBannerAdmin(BaseAdmin):
	pass

class IndexPromotionBannerAdmin(BaseAdmin):
	pass

class GoodsAdmin(BaseAdmin):
	pass

class GoodsSKUAdmin(BaseAdmin):
	pass

class GoodsImageAdmin(BaseAdmin):
	pass


admin.site.register(GoodsType,GoodsTypeAdmin)
admin.site.register(GoodsSKU,GoodsSKUAdmin)
admin.site.register(GoodsImage,GoodsImageAdmin)
admin.site.register(IndexGoodsBanner,IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner,IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)
admin.site.register(Goods)
