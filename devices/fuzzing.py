def mutable(stage):
    def wrap_f(func):
        def wrapper(self, *args, **kwargs):
            response = self.get_mutation(stage=stage)
            if response:
                print('Got mutation for stage %s' % stage)
            else:
                response = func(self, *args[1:], **kwargs)
            return response
        return wrapper
    return wrap_f
