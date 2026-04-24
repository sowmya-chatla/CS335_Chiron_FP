:expensive = 1000 * 1000 * 1000
:value = 42

match :value [
    10 [ forward 10 ]
    n if (:expensive > 0) [ forward 42 ]
    _ [ forward 0 ]
]