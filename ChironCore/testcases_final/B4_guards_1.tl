
:x = 7
match :x [
    n if (:n > 5) [ forward 7 ]
    _ [ forward 0 ]
]
