:angle = 60

match :angle [
    90 [ repeat 4 [ forward 50
                    left 90 ] ]
    60 [ repeat 6 [ forward 50
                    left 60 ] ]
    45 [ repeat 8 [ forward 50
                    left 45 ] ]
    _ [ forward 10 ]
]