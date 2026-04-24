:x = 10
:y = 0
if (:x > 5) [
    forward 50
] else [
    :z = :x / :y
    forward :z
]