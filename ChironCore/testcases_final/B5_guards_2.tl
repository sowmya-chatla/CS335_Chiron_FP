:x = 3
match :x [
    n if (:n > 5) [ forward 3 ]
    _ [ forward 5 ]
]
