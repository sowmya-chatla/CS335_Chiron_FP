:x = 7

match :x [
5 [ forward 5 ]
n if (n > 10) [ forward n ]
n [
forward n
left 90
]
_ [ forward 0 ]
]