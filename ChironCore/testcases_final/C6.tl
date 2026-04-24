:x = 8

match :x [
    n if ((:n > 5) || (1 / 0 > 2)) [ forward 8 ]
    _ [ forward 0 ]
]