# Simple test
```python
In [10]: counter = 0
    ...: for line in Example2.replace("|", "\\").split("\n"):
    ...:     print(" " * counter + line)
    ...:     counter += 1
    ...:

  __________
  \  __  __  \
   \ \  \\  \ \
    \ \__\\__\ \
     \          \
      \__________\
```

# Theory after just round the head
```
  __________  << Here the index 0
  \  __  __  \ << index 1
   \ \  \\  \ \  << index 2
    \ \__\\__\ \  ...
     \          \
      \__________\
```

after that we need a system for -1 to -x to looks like the [3d head](./01-SImpleHead.md)

## END of Work
```
In [73]: Example2 = """
    ...:  __________
    ...: |  __  __  |
    ...: | |0 ||0 | |
    ...: | |__||__| |
    ...: |   ____   |
    ...: |__________|
    ...: """

In [74]: # Head (Top)
    ...: counter = 1
    ...: depth = 1
    ...: for line in range(depth): # 3 depth
    ...:     if counter == 1:
    ...:         print("  " + " " * counter + "/", end="")
    ...:     else:
    ...:         print("  " + " " * counter + "/")
    ...:     counter -= 1
    ...:
    ...: # Head (Front)
    ...: counter = 0
    ...: for line in Example2.replace("|", "\\").split("\n"):
    ...:     if counter == 1: # First run/line:
    ...:         print("  " * counter + "/" + line.replace(" ", "") + "/")
    ...:     else:
    ...:         print(" " * counter + line)
    ...:     counter += 1
    ...:
   /
  /__________/
  \  __  __  \
   \ \0 \\0 \ \
    \ \__\\__\ \
     \   ____   \
      \__________\

```
