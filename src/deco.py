import functools


def log_execution(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        print(f"Executing {fn.__name__}")
        return fn(*args, **kwargs)

    return wrapper


@log_execution
def handler(event, context):
    return "OK"


if __name__ == "__main__":
    result = handler("event", "context")
    print(result)
