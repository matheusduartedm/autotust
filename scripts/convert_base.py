import pandas as pd
import csv


source = ["ONS","ONS","ONS","ONS","EPE","EPE","EPE","EPE","EPE"]


def convert_ger(tust_path, cycles):
    for cycle in range(len(cycles)):
        ger_example_path = tust_path + "\\" + cycles[cycle] + ".ger"
        with open(ger_example_path, "r") as ger_input:
            ger_lines = ger_input.readlines()

        final_line_index = len(ger_lines)

        col_type = []
        col_name = []
        col_must = []
        col_c = []
        col_d = []
        col_o = []
        col_s = []
        col_i = []
        col_discount = []
        col_month = []
        col_ceg = []
        col_ons = []
        col_e = []
        col_aux = []
        col_trans = []
        col_bus01 = []
        col_cycle = []
        col_source = []
        for i in range(1, final_line_index-1):
            line = ger_lines[i]
            if len(line) >= 75 and line[0] != "(":
                type_val = line[0:3]
                name = line[0:32].rstrip()
                must = line[32:41]
                c = line[41:42]
                d = line[42:43]
                o = line[43:44]
                s = line[44:45]
                i_val = line[45:46]
                discount = line[46:51]
                month = line[51:53]
                ceg = line[53:61]
                ons = line[61:66]
                e = line[66:67]
                aux = line[67:68]
                trans = line[68:69]
                bus01 = line[70:75]
                col_type.append(type_val)
                col_name.append(name)
                col_must.append(must)
                col_c.append(c)
                col_d.append(d)
                col_o.append(o)
                col_s.append(s)
                col_i.append(i_val)
                col_discount.append(discount)
                col_ceg.append(ceg)
                col_month.append(month)
                col_ons.append(ons)
                col_e.append(e)
                col_aux.append(aux)
                col_trans.append(trans)
                col_bus01.append(bus01)
                col_cycle.append(cycles[cycle][0:4])
                col_source.append(source[cycle])
        
        df_ger = pd.DataFrame({"CEG": col_ceg, "NOME": col_name, "TYPE": col_type, "MUST": col_must, "C": col_c,
                               "D": col_d, "O": col_o, "S": col_s, "I": col_i, "DISCOUNT": col_discount,
                               "MONTH": col_month, "ONS": col_ons, "E": col_e, "AUX": col_aux, "TRANS": col_trans,
                               "BUS01": col_bus01, "CYCLE": col_cycle, "SOURCE": col_source})
        
        csv_path = tust_path + "\\ger_" + cycles[cycle] + ".csv"
        df_ger.to_csv(csv_path, index=False)


def convert_dc(tust_path, cycles):
    for cycle in range(len(cycles)):
        aneel_example_path = tust_path + "\\" + cycles[cycle] + ".dc"
        with open(aneel_example_path, "r") as aneel_input:
            aneel_lines = aneel_input.readlines()

        final_line_index = 0
        for i in range(1, len(aneel_lines)):
            line = aneel_lines[i]
            if len(line) >= 5 and line[0:5] == "99999":
                final_line_index = i
                break

        col_number = []
        col_op = []
        col_type = []
        col_name = []
        col_volt = []
        col_phase = []
        col_must = []
        col_uf = []
        col_ss = []
        col_cycle = []
        col_source = []
        for i in range(3, final_line_index-1):
            line = aneel_lines[i]
            if len(line) >= 78 and line[0] != "(":
                number = line[0:5]
                op = line[6:7]
                type_val = line[7:8]
                name = line[10:21]
                volt = line[24:28]
                phase = line[28:32]
                must = line[32:37]
                uf = line[73:76]
                ss = line[76:78]
                col_number.append(number)
                col_op.append(op)
                col_type.append(type_val)
                col_name.append(name)
                col_volt.append(volt)
                col_phase.append(phase)
                col_must.append(must)
                col_uf.append(uf)
                col_ss.append(ss)
                col_cycle.append(cycles[cycle][0:4])
                col_source.append(source[cycle])

        df_dc = pd.DataFrame({"NUMBER": col_number, "OP": col_op, "TYPE": col_type, "NAME": col_name, "VOLT": col_volt,
                              "PHASE": col_phase, "MUST": col_must, "UF": col_uf, "SS": col_ss, "CYCLE": col_cycle,
                              "SOURCE": col_source})
        
        csv_path = tust_path + "\\dc_" + cycles[cycle] + ".csv"
        df_dc.to_csv(csv_path, index=False)

        first_line_index = 0
        for i in range(1, len(aneel_lines)):
            line = aneel_lines[i]
            if line[0:4] == "DLIN":
                first_line_index = i
                break

        final_line_index = 0
        for i in range(first_line_index, len(aneel_lines)):
            line = aneel_lines[i]
            if len(line) >= 5 and line[0:5] == "99999":
                final_line_index = i
                break

        col_de = []
        col_nome_de = []
        col_para = []
        col_nome_para = []
        col_circ = []
        col_est = []

        for i in range(first_line_index+2, final_line_index-1):
            line = aneel_lines[i]
            if len(line) >= 78 and line[0] != "(":
                de = line[0:5]
                nome_de = df_dc.loc[df_dc["NUMBER"] == de, "NAME"].values[0]
                para = line[10:15]
                nome_para = df_dc.loc[df_dc["NUMBER"] == para, "NAME"].values[0]
                circ = line[15:17]
                est = line[17:18]
                col_de.append(de)
                col_nome_de.append(nome_de)
                col_para.append(para)
                col_nome_para.append(nome_para)
                col_circ.append(circ)
                col_est.append(est)

        df_dlin = pd.DataFrame({"DE": col_de, "NOME_DE": col_nome_de, "PARA": col_para, "NOME_PARA": col_nome_para,
                                "CIRC": col_circ, "EST": col_est})
        
        csv_path = tust_path + "\\dlin_" + cycles[cycle] + ".csv"
        df_dlin.to_csv(csv_path, index=False)


def convert_tuh(tust_path, cycles):
    for cycle in range(len(cycles)):
        aneel_example_path = tust_path + "\\" + cycles[cycle] + ".tuh"
        with open(aneel_example_path, "r") as aneel_input:
            aneel_lines = aneel_input.readlines()

        final_line_index = len(aneel_lines)-1

        col_name = []
        col_ceg = []
        col_tust = []
        col_cycle = []
        col_source = []
        for i in range(11, final_line_index-1):
            line = aneel_lines[i]
            name = line[3:33].rstrip()
            ceg = line[36:43]
            tust = line[126:132]
            col_name.append(name)
            col_ceg.append(ceg)
            col_tust.append(tust)
            col_cycle.append(cycles[cycle][0:4])
            col_source.append(source[cycle])

        df_tuh = pd.DataFrame({"CEG": col_ceg, "NAME": col_name, "TUST": col_tust, "CYCLE": col_cycle,
                               "SOURCE": col_source})
        
        csv_path = tust_path + "\\tuh_" + cycles[cycle] + ".csv"
        df_tuh.to_csv(csv_path, index=False)


def convert_nos(tust_path, cycles):
    for cycle in range(len(cycles)):
        aneel_example_path = tust_path + "\\" + cycles[cycle] + ".nos"
        with open(aneel_example_path, "r") as aneel_input:
            aneel_lines = aneel_input.readlines()

        final_line_index = len(aneel_lines)-9

        col_number = []
        col_name = []
        col_tustb = []
        col_cycle = []
        col_source = []

        for i in range(12, final_line_index-1):
            line = aneel_lines[i]
            number = line[2:7]
            name = line[8:20]
            tustb = line[34:43]
            col_number.append(number)
            col_name.append(name)
            col_tustb.append(tustb)
            col_cycle.append(cycles[cycle][0:4])
            col_source.append(source[cycle])

        df_nos = pd.DataFrame({"NUMBER": col_number, "NAME": col_name, "TUSTB": col_tustb, "CYCLE": col_cycle,
                               "SOURCE": col_source})
        
        csv_path = tust_path + "\\nos_" + cycles[cycle] + ".csv"
        df_nos.to_csv(csv_path, index=False)


def run(tust_path, cycles):
    convert_ger(tust_path, cycles)
    convert_dc(tust_path, cycles)
    convert_tuh(tust_path, cycles)
    convert_nos(tust_path, cycles)


if __name__ == "__main__":
	run()