:cost = 3 + 4
:x = 99

match :x [
    n if (:cost > 0) [ forward :cost ]
    _ [ forward 0 ]
]