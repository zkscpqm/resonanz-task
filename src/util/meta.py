class SingletonMeta(type):
    """
    Metaclass for creating singletons. Only used for the web app as a precaution.
    """

    _instances: dict[str, object] = {}

    def __call__(cls, *args, **kwargs) -> object:
        if cls.__name__ not in cls._instances:
            cls._instances[cls.__name__] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls.__name__]
