import numpy as np

class ascii:
    def __init__(self, art):
        self.art = art
        self.length = art.count('\n')
        self.width = max([len(line) for line in art.split('\n')])
        self.matrix = np.zeros((self.turned_length, self.turned_width)) # Temporal

    def turn_left_down(self):
        pass

# Head (Top)
counter = 1
depth = 1
for line in range(depth): # 3 depth
    if counter == 1:
        print("  " + " " * counter + "/", end="")
    else:
        print("  " + " " * counter + "/")
    counter -= 1

# Head (Front)
counter = 0
for line in Example2.replace("|", "\\").split("\n"):
    if counter == 1: # First run/line:
        print("  " * counter + "/" + line.replace(" ", "") + "/")
    else:
        print(" " * counter + line)
    counter += 1
