:a = 3
:b = 20
if ((:a > 10) && (:b > 10)) [
    forward 80
] else [
    forward 30
]

:x = 0
:y = 8
if ((:x > 5) || (:y > 5)) [
    forward 50
] else [
    forward 10
]

:x = 5
:y = 10
if ((:x > 0) || (:y > 3)) [
    forward 60
] else [
    forward 10
]