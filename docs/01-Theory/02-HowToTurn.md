# Should be large
first of all we cant do that with 3x3 art! it should be at last 6x12
like:
```
                  __________ 
 __________      /         /\  
|  __  __  |    /_________/  \ 
| |  ||  | |    \  __  __ \   \
| |__||__| |     \ \ \ \ \ \   \
|          |      \ \_\ \_\ \  / 
|__________|       \_________\/  
```

# How to count length?
one line will add to the head it's stable for other example for example:
```Invader
  >>> ____ <<<<<<<<<<NEW LINE
     /___/\_                                __
    _\   \/_/\__                          _|  |_
  __\       \/_/\                       _|      |_
  \   __    __ \ \                     |  _    _  |
 __\  \_\   \_\ \ \   __               | |_|  |_| |
/_/\\   __   __  \ \_/_/\           _  |  _    _  |  _
\_\/_\__\/\__\/\__\/_\_\/          |_|_|_| |__| |_|_|_|
   \_\/_/\       /_\_\/              |_|_        _|_|
      \_\/       \_\/                  |_|      |_|
```
```
     NEW LINE>>>> ___________ <<<
 __________      /         / \  
|  __  __  |    /_________/   \ 
| |  ||  | |    \  __  __ \    \
| |__||__| |     \ \ \ \ \ \    \
|          |      \ \_\ \_\ \  // 
|__________|       \_________  /  
```
```
   >> __ <<<<<NEW LINE
 _   /_/\
|_|  \_\/
```
simple yeah?! just add a line to the top

### here the formole:
`turned_length = lenght+1`

# How to calculate width?
it's depends on count of lines for e.x.:
```
          > __
 2> _    3>/_/\
  >|_|    >\_\/
   ^^^     ^^^^
    3        4
```

```
          > _
  > _     >/_/\
 4>| |   5>\ \ \
  >| |    > \ \ \
  >|_|    >  \_\/
   ^^^     ^^^^^^
    3         6
```
```
          > _
  > _     >/_/\
  >| |    >\ \ \
  >| |    > \ \ \
  >| |    >  \ \ \
  >| |    >   \ \ \
  >| |    >    \ \ \
  >| |    >     \ \ \
15>| |  16>      \ \ \
  >| |    >       \ \ \
  >| |    >        \ \ \
  >| |    >         \ \ \
  >| |    >          \ \ \
  >| |    >           \ \ \
  >| |    >            \ \ \
  >|_|    >             \_\/
   ^^^     ^^^^^^^^^^^^^^^^^
    3             17
```

### here the formole:
`turned_wigth = lenght+widght-1`



# inside of bod is diffrent of outside:
TODO

# continue
```
            _   _
 _  _      /_/\/_/\
|_||_|     \_\/\_\/
```
it's false!!!
```
            _  _
 _  _      /_//_/\
|_||_|     \_\\_\/
```
it's True!!!
-------------
```
             _   _
 _   _      /_/\/_/\
|_| |_|     \_\/\_\/
   ^^          ^^
   space!      SPACE!
```

# not only cubes!
```square
          _
 _       / /\
| |      \ \ \
|_|       \_\/
```
```square
          ______
 ___     /_____/\
|___|    \_____\/
```


