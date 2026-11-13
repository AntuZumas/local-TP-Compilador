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
    v_avanceok DB "avanceok", 0
    v_2_i DW 2
    v_10_i DW 10
    v_32767_i DW 32767
    v_1_25sm2 DD 0.0125
    v__5 DD 0.5
    v_0_i DW 0
    v_1_i DW 1
    v_m32768_i DW -32768
    v_3_i DW 3
    v_base_grupo40 DW 0
    v_tope_grupo40 DW 0
    v_resultado_grupo40 DW 0
    v_aux_grupo40 DW 0
    v_promedio_grupo40 DD 0.0
    v_x_grupo40_origen_metodo DW 0
    v_y_grupo40_origen_metodo DD 0.0
    v_local_grupo40_origen_metodo DW 0
    v_p_grupo40_calcular DW 0
    v_q_grupo40_calcular DW 0
    v_r_grupo40_calcular DD 0.0
    v_temp_grupo40_calcular DW 0
    v_item_grupo40_0 DW 0
    v_item_grupo40_1 DW 0
    v_item_grupo40_2 DW 0
    v_item_grupo40_3 DD 0.0
    v__aux_aux1 DW 0
    v__aux_aux2 DW 0
    v__aux_aux3 DW 0
    v__aux_aux4 DW 0
    v__aux_aux5 DW 0
    v__aux_aux6 DD 0.0
    v__aux_aux7 DW 0
    v__aux_aux8 DW 0
    v__aux_aux9 DW 0

.code
start:
    FINIT
; --- BEGIN_MAIN (grupo40) ---
    MOV AX, v_10_i
    MOV v_base_grupo40, AX
    MOV AX, v_32767_i
    MOV v_tope_grupo40, AX
    FLD v_1_25sm2
    FADD v__5
    FSTP v__aux_aux6
    FLD v__aux_aux6
    FABS
    FCOMP _flt_max_single
    FSTSW AX
    SAHF
    JA _err_overflow_suma_flt
    FLD v__aux_aux6
    FSTP v_promedio_grupo40
    MOV AX, v_10_i
    MOV v_item_grupo40_0, AX
    MOV AX, v_m32768_i
    MOV v_item_grupo40_1, AX
L_step_53:
L_step_53: ; REPEAT_START [53]
    MOV AX, v_10_i
    ADD AX, v_1_i
    MOV v__aux_aux7, AX
    MOV AX, v__aux_aux7
    MOV v_aux_grupo40, AX
    MOV AX, v_aux_grupo40
    MOV v_q_grupo40_calcular, AX
    MOV AX, v_item_grupo40_0
    MOV v_p_grupo40_calcular, AX
    FLD v_promedio_grupo40
    FSTP v_r_grupo40_calcular
    CALL v_calcular_grupo40
    MOV v__aux_aux8, AX
    MOV AX, v__aux_aux8
    MOV v_resultado_grupo40, AX
    MOV AX, v_resultado_grupo40
    MOV v_x_grupo40_origen_metodo, AX
    FLD v_promedio_grupo40
    FSTP v_y_grupo40_origen_metodo
    CALL v_metodo_grupo40_origen
    MOV v__aux_aux9, AX
    invoke crt_printf, addr _fmt_str, addr v_avanceok
    MOV AX, v_resultado_grupo40
    CMP AX, v_0_i
    JE L_step_53
    MOVSX EAX, v_resultado_grupo40
    invoke crt_printf, addr _fmt_int, EAX
; --- END_MAIN (grupo40) ---
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

v_metodo_grupo40_origen PROC
    ; toi(y:grupo40:origen:metodo) -> @aux1 con control (g) de pérdida de información
    FLD v_y_grupo40_origen_metodo
    FCOM _flt_max_int
    FSTSW AX
    SAHF
    JA _err_perdida_info_toi
    FCOM _flt_min_int
    FSTSW AX
    SAHF
    JB _err_perdida_info_toi
    FISTP v__aux_aux1
    FILD v__aux_aux1
    FLD v_y_grupo40_origen_metodo
    FCOMPP
    FSTSW AX
    SAHF
    JNE _err_perdida_info_toi
    MOV AX, v_x_grupo40_origen_metodo
    ADD AX, v__aux_aux1
    MOV v__aux_aux2, AX
    MOV AX, v__aux_aux2
    MOV v_local_grupo40_origen_metodo, AX
    MOV AX, v_local_grupo40_origen_metodo
    RET
    RET
v_metodo_grupo40_origen ENDP
v_calcular_grupo40 PROC
    MOV AX, v_p_grupo40_calcular
    CMP AX, v_q_grupo40_calcular
    JL L_step_28
    MOV AX, v_q_grupo40_calcular
    IMUL v_2_i
    JO _err_overflow_prod_int
    MOV v__aux_aux3, AX
    MOV AX, v__aux_aux3
    MOV v_aux_grupo40, AX
    MOV AX, v_p_grupo40_calcular
    ADD AX, v_aux_grupo40
    MOV v__aux_aux4, AX
    MOV AX, v__aux_aux4
    MOV v_temp_grupo40_calcular, AX
    JMP L_step_32
L_step_28:
    ; toi(r:grupo40:calcular) -> @aux5 con control (g) de pérdida de información
    FLD v_r_grupo40_calcular
    FCOM _flt_max_int
    FSTSW AX
    SAHF
    JA _err_perdida_info_toi
    FCOM _flt_min_int
    FSTSW AX
    SAHF
    JB _err_perdida_info_toi
    FISTP v__aux_aux5
    FILD v__aux_aux5
    FLD v_r_grupo40_calcular
    FCOMPP
    FSTSW AX
    SAHF
    JNE _err_perdida_info_toi
    MOV AX, v__aux_aux5
    MOV v_temp_grupo40_calcular, AX
L_step_32:
    MOV AX, v_temp_grupo40_calcular
    RET
    RET
v_calcular_grupo40 ENDP
end start
