.model small
.data
var_a    dw    1
var_b    dw    2

start:
cmp a, 0
jge J0
mov var_a, 0
J0:
mov var_b, 3

end start
end