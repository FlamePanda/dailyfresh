from django.conf import settings
import  os
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
from alipay.aop.api.response.AlipayTradeQueryResponse import AlipayTradeQueryResponse

# 获取公钥和私钥的路径
ALIPAY_KEY_PATH = os.path.join(settings.BASE_DIR,'utils/app_alipay_public_key.pem')
APP_KEY_PRIVATE_PATH = os.path.join(settings.BASE_DIR,'utils/app_private_key.pem')

class Alipay(object):
	@classmethod
	def get_pay_url(cls,order_id,total_amount):
		# 获取内容
		with open(ALIPAY_KEY_PATH) as f:
			alipay_public_key = f.read()

		with open(APP_KEY_PRIVATE_PATH) as f:
			app_private_key = f.read()

		#  设置配置，包括支付宝网关地址、app_id、应用私钥、支付宝公钥;
		config = AlipayClientConfig()
		config.server_url = settings.SERVER_URL
		config.app_id = settings.APP_ID
		config.app_private_key = app_private_key 
		config.alipay_public_key= alipay_public_key

		# 得到
		client = DefaultAlipayClient(alipay_client_config=config)
		model = AlipayTradePagePayModel()
		model.out_trade_no = order_id
		model.total_amount = str(total_amount)
		model.subject = "天天生鲜-%s"%order_id
		model.product_code= "FAST_INSTANT_TRADE_PAY"
		model.body = '天天生鲜'
		request = AlipayTradePagePayRequest(biz_model=model)
		# 得到构造的请求，如果http_method是GET，则是一个带完成请求参数的url
		response_url = client.page_execute(request,http_method="GET")
		return response_url

	@classmethod
	def get_pay_status(cls,order_id):
		# 获取内容
		with open(ALIPAY_KEY_PATH) as f:
			alipay_public_key = f.read()

		with open(APP_KEY_PRIVATE_PATH) as f:
			app_private_key = f.read()

		#  设置配置，包括支付宝网关地址、app_id、应用私钥、支付宝公钥;
		config = AlipayClientConfig()
		config.server_url = settings.SERVER_URL
		config.app_id = settings.APP_ID
		config.app_private_key = app_private_key 
		config.alipay_public_key= alipay_public_key

		# 得到
		client = DefaultAlipayClient(alipay_client_config=config)
		model = AlipayTradeQueryModel()
		model.out_trade_no = order_id
		request = AlipayTradeQueryRequest(biz_model=model)
		# 得到构造的请求,获取返回内容
		import time
		i = 1
		while True:
			time.sleep(10)
			response_content = None
			try:
				response_content = client.execute(request)
			except Exception as ex:
				print(ex)
			if not response_content:
				return None
			else:
				# 解析相应结果
				response = AlipayTradeQueryResponse()
				response.parse_response_content(response_content)
				if response.is_success() and response.trade_status == 'TRADE_SUCCESS':
					return response.trade_no
				i += 1
				if i == 30:
					# 五分钟后还是失败
					# 判定支付失败
					return None
