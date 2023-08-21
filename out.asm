.model small
.data
var_x dw 1
var_a dw 2

.code
start:

mov AH, 1h ; ожидать ввода любого символа
int 21h
mov AX, 4c00h ; завершение программы
int 21h
end start
end