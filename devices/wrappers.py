import traceback


def mutable(stage):
    def wrap_f(func):
        def wrapper(self, *args, **kwargs):
            data = kwargs.get('fuzzing_data', None)
            response = self.get_mutation(stage=stage, data=data)
            try:
                if response:
                    print('[+] Got mutation for stage %s' % stage)
                else:
                    print('[*] Calling %-30s "%s"' % (func.__name__, stage))
                    response = func(self, *args, **kwargs)
            except Exception as e:
                print(traceback.format_exc())
                print(''.join(traceback.format_stack()))
                raise e
            return response
        return wrapper
    return wrap_f
