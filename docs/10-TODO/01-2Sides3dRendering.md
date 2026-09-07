> **STATUS (v0.1.0):** implemented! Use `shade=True` (depth gradient) or
> `fill='/'` (uniform texture) to get exactly this behaviour -- see the
> [Usage](../02-Usage/00-usage.md#shading) page. The notes below are the
> original design sketch.

```
|         |||||
|         |||||
----      -----
|  |      |   |
```
- it should show the depth with white-gray-black from 0 to 1
```
  /////
 /////
/////

# RUBIK
```
                   _________
                  /__/__/__/\
 __________      /__/__/__/\/\  
|   |  |   |    /__/__/__/\/\/\ 
|   |  |   |    \__\__\__\/\/\/ 
|   |  |   |     \__\__\__\/\/  
|   |  |   |      \__\__\__\/ 
|___|__|___|
```