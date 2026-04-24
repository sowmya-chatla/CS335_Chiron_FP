:expensive = 1000 * 1000 * 1000
:value = 10

match :value [
    10 [ forward 10 ]
    n if (:expensive > 0) [ forward 200 ]
    _ [ forward 0 ]
]