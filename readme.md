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
...     @Attention.schedule(days = 0, hours = 0, minutes = 0, seconds = 1)      # Tell Attention handler this method should be called instantly for every 1 seconds.
...     def update(self):
...         self.tstamp += 1
...
>>> a = A(a = 3)
>>> a.tstamp
4                       # 1 second later
>>> a.tstamp
6                       # 3 seconds later
>>> a.unsubscribe()     # Disable all routine methods
```