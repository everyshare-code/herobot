import datetime

def timestamp(func):
    def wrapper(message, *args, **kwargs):
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message.time = current_time
        return func(message, *args, **kwargs)
    return wrapper
