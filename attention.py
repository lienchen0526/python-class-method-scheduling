from functools import wraps, WRAPPER_ASSIGNMENTS
import threading
from typing import Union, List, Tuple
from collections.abc import Callable
from time import sleep
from datetime import timedelta, datetime

try:
    from schedule import Scheduler, Job
except ModuleNotFoundError:
    import pip
    pip.main(['install', 'schedule==1.0.0'])

class Attention(object):
    def __init__(self):
        self._pool = []
    
    @staticmethod
    def schedule(
        interval: Union[None, timedelta] = None,
        standfor: Union[None, timedelta] = None,
        until: Union[None, datetime] = None,
        group: int = 0
    ):
        assert isinstance(interval, timedelta), f':interval: argument should be an instance of <datetime.timedelta>, but {type(interval)} is detected with value: {interval}'
        assert not (standfor and until), f':standfor: argument cannot appear with :until: argument'
        if standfor:
            assert isinstance(standfor, timedelta), f':interval: argument should be an instance of <datetime.timedelta>, but {type(standfor)} is detected with value: {standfor}'
        if until:
            assert isinstance(until, datetime), f':until: argument should be an instance of <datetime.datetime>, but {type(until)} is detected with value: {until}'
            standfor = until - datetime.now()
        
        def label(method):
            setattr(method, 
                    '__schinterval__', 
                    {
                        'delta': interval.total_seconds(),
                        'standfor': standfor.total_seconds() if isinstance(standfor, timedelta) else 0
                    }
                )
            setattr(method, '__schgroup__', {'group': group})
            return method
        return label
    
    @staticmethod
    def trigger(meth_or_grp: Union[Callable, int, Tuple[int]]):
        if isinstance(meth_or_grp, int):
            def label(method):
                setattr(method, '__schtrigger__', {'group': (meth_or_grp)})
                setattr(method, '__trigger__', True)
                return method
            return label
        assert callable(meth_or_grp), f'{meth_or_grp.__name__} is not callable'
        setattr(meth_or_grp, '__trigger__', True)
        return meth_or_grp
    
    def __call__(self, Cls = None):
        class Wrapped(Cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                assignments = filter(
                    lambda x: hasattr(Cls, x), WRAPPER_ASSIGNMENTS
                )
                for attr in assignments:
                    setattr(self, attr, getattr(Cls, attr))
                
                self._onschmethods =\
                    [getattr(self, x) for x in dir(self) if \
                     hasattr(getattr(self, x), '__schinterval__')]
                
                self._triggers =\
                    [getattr(self, x) for x in dir(self) if \
                     hasattr(getattr(self, x), '__trigger__')]
                
                self._schlock = threading.Lock() # For Accessing scheduler jobs queue
                self._schback = Scheduler()

                self._schkillers = [
                    threading.Timer(
                        interval = getattr(x, '__schinterval__').get('standfor'),
                        function = self.unsubscribe,
                        args = [x]
                    ) for x in self._onschmethods if getattr(x, '__schinterval__').get('standfor')
                ]

                self._schrunner = threading.Thread(
                    target = self._schmain,
                    daemon = True
                )
                
                self._schrunner.start()
                for killer in self._schkillers:
                    killer.daemon = True
                    killer.start()
            
            def _schmain(self):
                for method in self._onschmethods:
                    meth_delta = method.__schinterval__.get('delta', 0)
                    if meth_delta > 0:
                        Job(
                            interval = meth_delta, 
                            scheduler = self._schback
                        ).seconds.do(method).tag(method.__name__)
                    else: pass
                while True:
                    with self._schlock:
                        self._schback.run_pending()
                    sleep(0.5)
            
            def unsubscribe(self, method: Union[None, str, Callable] = None) -> int:
                if not method:
                    with self._schlock:
                        self._schback.clear()
                    return 1
                if callable(method):
                    with self._schlock:
                        self._schback.clear(method.__name__)
                    return 1
                if type(method) == str:
                    with self._schlock:
                        self._schback.clear(method)
                    return 1
                return -1

        return Wrapped

def InstanceKeeper(cls_):
    class WrapedCLS(cls_):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            assignments = filter(
                lambda x: hasattr(cls_, x), WRAPPER_ASSIGNMENTS
            )
            for attr in assignments:
                setattr(self, attr, getattr(cls_, attr))
            
            self._keepers = threading.Thread()
        
        def startkeeperjob(self, callable_: Callable, *args, **kwargs):
            if not callable(callable_):
                raise TypeError(f'The type of callable_: {type(callable_)} is not callable')

            if not hasattr(self, callable_.__name__):
                raise NameError(f'The current instance does not have the method name {callable_.__name__}.')
            
            _local_method = getattr(self, callable_.__name__)

            if not _local_method == callable_:
                raise UnboundLocalError(f':callable_: method can not be controlled by the instance.')
            
            threading.Thread(
                target = callable_,
                args = args,
                kwargs = kwargs,
                daemon = True
            ).start()

    return WrapedCLS