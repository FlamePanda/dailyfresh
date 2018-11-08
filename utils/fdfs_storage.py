from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client

class MyStorage(Storage):
	'''自定义文件存储类'''
	def __init__(self,fdfs_client_conf=None,base_url=None):
		'''初始化fastdfs客户端的配置文件和对应文件服务器的url'''
		if not fdfs_client_conf:
			self.fdfs_client_conf = settings.FDFS_CLIENT_CONF
		if not base_url:
			self.base_url = settings.BASE_URL

	def _open(self,name, mode='rb'):
		'''返回文件对象'''
		pass
	
	def _save(self,name, content):
		'''保存文件至fastDFS系统'''
		# 获取storage client 对象
		client = Fdfs_client(self.fdfs_client_conf)
		# 上传文件
		ret = client.upload_by_buffer(content.read())
		# 判断是否上传成功
		if not ret or ret.get('Status') != 'Upload successed.':
			raise Exception('文件上传失败！')
		else:
			filename = ret.get('Remote file_id').decode()
			print('name:',name)
			print('filename',filename)
		return filename

	def exists(self,name):
		'''判断文件是否可用'''
		return False

	def url(self,name):
		'''文件内容的URL'''
		return self.base_url + name
	
	def delete(self,name):
		'''删除文件'''
		# 获取storage client 对象
		client = Fdfs_client(self.fdfs_client_conf)
		# 删除文件
		print('delete:',name)
		ret = client.delete_file(name)
		print(ret)
		
