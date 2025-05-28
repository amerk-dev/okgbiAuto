from loguru import logger

@logger.catch
def foo(n):
    n / 0


foo(2)