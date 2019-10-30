import logging

def create_logger(name, file, loglevel=logging.NOTSET):
	logging.basicConfig(level=loglevel,filename=file, format='%(asctime)s %(levelname)s %(filename)s %(funcName)s - %(message)s')