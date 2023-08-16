.model small
.data
var_a dw 1
var_b dw 2

.code
start:
cmp var_a, 0
jge J0
mov var_a, 0
J0:
mov var_b, 3

mov AH, 1h ; ожидать ввода любого символа
int 21h
mov AX, 4c00h ; завершение программы
int 21h
end start
end