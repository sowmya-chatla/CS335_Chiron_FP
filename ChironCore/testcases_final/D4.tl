:exp = 1000 * 1000 * 1000

match :x [
    0 [ forward 0 ]
    n if (:exp > :n) [ forward :n ]
    _ [ forward 1 ]
]