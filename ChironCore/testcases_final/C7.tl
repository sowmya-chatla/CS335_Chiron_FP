:x = 5

match :x [
    n [ :x = 99
        forward :n
        right :x 
    ]
]