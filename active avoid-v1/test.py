import re
import re

position = '15  ,  36'
p = re.findall(r"\d+.?\d*",position)

print(p)
print(p[0])