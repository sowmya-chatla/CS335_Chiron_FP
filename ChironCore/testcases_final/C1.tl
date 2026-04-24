:x = 5 + 5

match :x [
    10 [ forward 10 ]
    _ [ forward 0 ]
]