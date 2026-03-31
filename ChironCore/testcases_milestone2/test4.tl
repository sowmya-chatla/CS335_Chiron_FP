:x = 3

match :x [
    n if (n > 5) [ forward n ]
    _ [ forward 5 ]
]