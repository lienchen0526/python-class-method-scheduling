from functools import wraps, WRAPPER_ASSIGNMENTS
import threading
from typing import Union, List, Tuple
from collections.abc import Callable
from schedule import Scheduler, Job
from time import sleep
import atexit

class Attention(object):
    def __init__(self):
        self._pool = []
    
    @staticmethod
    def schedule(
        days: Union[int, None] = 0, 
        hours: Union[int, None] = 0,
        minutes: Union[int, None] = 0,
        seconds: Union[int, None] = 0,
        lastfor: int = 0,
        group: int = 0
    ):
        def label(method):
            setattr(method, 
                    '__schinterval__', 
                    {
                        'delta': days * 24 * 3600 + hours * 3600 + minutes * 60 + seconds,
                        'lastfor': lastfor,
                        'keepasjob': True
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
                
                self._schback = Scheduler()
                self._schtrd = threading.Thread(
                    target = self._schmain,
                    daemon = True
                )
                
                self._schtrd.start()
            
            def _schmain(self):
                self._ongoing = True
                for method in self._onschmethods:
                    meth_delta = method.__schinterval__.get('delta', 0)
                    if meth_delta > 0:
                        Job(
                            interval = meth_delta, 
                            scheduler = self._schback
                        ).seconds.do(method).tag(method.__name__)
                    else: pass
                while self._ongoing:
                    self._schback.run_pending()
                    sleep(1)
            
            def unsubscribe(self, method: Union[None, str] = None):
                if not method:
                    self._schback.clear()
                    self._ongoing = False
                    self._schtrd.join()
                else:
                    assert type(method) == str, f'Method name must be string or callable'
                    self._schback.clear(method)
                pass

            def __exit__(self):
                print("exit is calling")
            def __del__(self):
                print("del is calling")
        return Wrapped