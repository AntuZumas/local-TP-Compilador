.386
.model flat, stdcall
option casemap :none
include \masm32\include\masm32rt.inc

.data
    _flt_max_single DD 3.40282347e38
    _flt_max_int    DD 32767.0
    _flt_min_int    DD -32768.0
    _print_flt_buf  DQ 0.0
    _fmt_int        DB "%d", 13, 10, 0
    _fmt_flt        DB "%g", 13, 10, 0
    _fmt_str        DB "%s", 13, 10, 0
    _msg_div_cero   DB "Error en tiempo de ejecucion (a): Division por cero.", 13, 10, 0
    _msg_ovf_flt    DB "Error en tiempo de ejecucion (c): Overflow en suma de punto flotante.", 13, 10, 0
    _msg_ovf_int    DB "Error en tiempo de ejecucion (d): Overflow en producto de enteros.", 13, 10, 0
    _msg_toi_loss   DB "Error en tiempo de ejecucion (g): Perdida de informacion en conversion toi.", 13, 10, 0
    v_7_i DW 7
    v_2_i DW 2
    v_3_i DW 3
    v_precio_demo DW 0
    v__aux_aux1 DW 0
    v__aux_aux2 DW 0

.code
start:
    FINIT
; --- BEGIN_MAIN (demo) ---
    MOV AX, v_2_i
    IMUL v_3_i
    JO _err_overflow_prod_int
    MOV v__aux_aux1, AX
    MOV AX, v_7_i
    ADD AX, v__aux_aux1
    MOV v__aux_aux2, AX
    MOV AX, v__aux_aux2
    MOV v_precio_demo, AX
    MOVSX EAX, v_precio_demo
    invoke crt_printf, addr _fmt_int, EAX
; --- END_MAIN (demo) ---
    invoke ExitProcess, 0
_err_div_cero:
    invoke StdOut, addr _msg_div_cero
    invoke ExitProcess, 1
_err_overflow_suma_flt:
    invoke StdOut, addr _msg_ovf_flt
    invoke ExitProcess, 1
_err_overflow_prod_int:
    invoke StdOut, addr _msg_ovf_int
    invoke ExitProcess, 1
_err_perdida_info_toi:
    invoke StdOut, addr _msg_toi_loss
    invoke ExitProcess, 1

end start
