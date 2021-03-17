# Introduction

This modules provide some class tools may be useful

# Modules
## attention
attention is a module that help you to automated some method of your self-defined class.

```
>>> from attention import Attention
>>> @Attention()                                                                # Initialize a Attention class that tell module that there are some methods to be schedule
... class A:
...     def __init__(self, a = None):
...         self.tstamp = a if a else 1
...         self.sstamp = 0
...
...     @Attention.schedule(
...         interval = datetime.timedelta(minutes = 1),
...         standfor = datetime.timedelta(hours = 1)
...     )                                                                       # Tell Attention handler this method should be called instantly for every 1 minutes in the following one hour
...     def update(self):
...         self.tstamp += 1
...
...     @Attention.schedule(
...         interval = datetime.timedelta(minutes = 2),
...         until = datetime.datetime(year = 2022, month = 5, day = 26)
...     )
...     def s_update(self):
...         self.sstamp -= 1
>>> a = A(a = 3)
>>> a.tstamp
4                       # 1 second later
>>> a.tstamp
6                       # 3 seconds later
>>> a.unsubscribe()     # Disable all routine methods
```