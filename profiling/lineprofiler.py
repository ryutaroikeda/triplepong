# Adapted from https://zapier.com/engineering/profiling-python-boss/
try:
    from line_profiler import LineProfiler
    def do_profile(follow=[]):
        def inner(func):
            def profiled(*args, **kwargs):
                try:
                    profiler=LineProfiler()
                    profiler.add_function(func)
                    for f in follow:
                        profiler.add_function(f)
                    profiler.enable_by_count()
                    return func(*args, **kwargs)
                finally:
                    profiler.print_stats()
            return profiled
        return inner

except ImportError:
    def do_profile(follow=[]):
        def f(func):
            def p(*args, **kwargs):
                return func(*args, **kwargs)
            return p
        return f

