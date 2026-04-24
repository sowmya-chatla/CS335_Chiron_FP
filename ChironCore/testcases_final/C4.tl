:x = 10

match :x [
    n [ :x = :x + 1
        forward :x ]
]