:x = 5

match :x [
    5 [ forward 5 ]
    n if (:n > 10) [ forward 20 ]
    n [ forward 99 ]
    _ [ forward 0 ]
]
