:exp = 1000 * 1000
:x = 2
:acc = 0

repeat :x [
    :acc = :acc + 5
]

match :acc [
    n if (:exp > 0) [
        :acc = :acc + 1
    ]
]

if (:acc > 0) [
    forward :acc
]