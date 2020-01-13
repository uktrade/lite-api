from functools import wraps


def none_param_tester(*params):
    """
    Runs the decorated test n times depending on how many params are given
    Each run it sets one of the params to None
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            params_new = list(params)

            for i in range(len(params)):
                if i != 0:
                    params_newest = params_new.copy()
                    params_newest[i] = None
                    args2 = args + tuple(params_newest)
                    setattr(func, func.__name__ + str(params_new[i]), func(*args2))

            params_new[0] = None
            params_new = tuple(params_new)

            args = args + params_new
            return func(*args, **kwargs)

        return wrapper

    return decorator
