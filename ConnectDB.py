import pymysql
import pymysql.cursors

class DbUtil:
	@staticmethod
	def get_connection():
		try:
			db = pymysql.connect(host='localhost', user='root', password='root', db='burkhalter_yannis_ecommerce_bd_104', cursorclass=pymysql.cursors.DictCursor)
		except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
			print("BD NON CONNECTEE, Il y a une ERREUR : %s", error)
			print('Exception number: {}, value {!r}'.format(error.args[0], error))
		else:
			return db