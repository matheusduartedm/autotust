using DataFrames
using CSV

source = ["ONS","ONS","ONS","ONS","EPE","EPE","EPE","EPE","EPE"]

function convert_all_base(tust_path,cycles)
    convert_ger(tust_path, cycles)
    convert_dc(tust_path, cycles)
    convert_tuh(tust_path, cycles)
    convert_nos(tust_path, cycles)
end

function convert_ger(tust_path, cycles)

    for cycle in 1:length(cycles)
        ger_example_path = joinpath(tust_path, cycles[cycle]* ".ger")
        ger_input = open(ger_example_path,"r")
        ger_lines = readlines(ger_input)
        close(ger_input)

        final_line_index = length(ger_lines)

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
        for i in 2:final_line_index-2
            line = ger_lines[i]
            if length(line) >= 75 && line[1:1]!="("
                type = line[1:3]
                name = rstrip(line[1:32])
                must = line[33:41]
                c = line[42:42]
                d = line[43:43]
                o = line[44:44]
                s = line[45:45]
                i = line[46:46]
                discount = line[47:51]
                month = line[52:53]
                ceg = line[54:61]
                ons = line[62:66]
                e = line[67:67]
                aux = line[68:68]
                trans = line[69:69]
                bus01 = line[71:75]
                push!(col_type, type)
                push!(col_name, name)
                push!(col_must, must)
                push!(col_c, c)
                push!(col_d, d)
                push!(col_o, o)
                push!(col_s, s)
                push!(col_i, i)
                push!(col_discount, discount)
                push!(col_ceg, ceg)
                push!(col_month, month)
                push!(col_ons, ons)
                push!(col_e, e)
                push!(col_aux, aux)
                push!(col_trans, trans)
                push!(col_bus01, bus01)
                push!(col_cycle, cycles[cycle][1:4])
                push!(col_source, source[cycle])
            end
        end
        df_ger = DataFrame(CEG = col_ceg, NOME = col_name, TYPE = col_type, MUST = col_must, C = col_c, D = col_d, O = col_o, S = col_s, I = col_i, DISCOUNT = col_discount, MONTH = col_month, ONS = col_ons, E = col_e, AUX = col_aux, TRANS = col_trans, BUS01 = col_bus01, CYCLE = col_cycle, SOURCE = col_source)
        csv_path = joinpath(tust_path, "ger_" * cycles[cycle] * ".csv")
        CSV.write(csv_path, df_ger)
    end
end

function convert_dc(tust_path, cycles)
    for cycle in 1:length(cycles)
        aneel_example_path = joinpath(tust_path, cycles[cycle] * ".dc")
        aneel_input = open(aneel_example_path,"r")
        aneel_lines = readlines(aneel_input)
        close(aneel_input)

        final_line_index = 0
        for i in 2:length(aneel_lines)
            line = aneel_lines[i]
            if length(line)>= 5 && line[1:5] == "99999"
                final_line_index = i
                break
            end
        end
        final_line_index

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
        for i in 4:final_line_index-2
            line = aneel_lines[i]
            if length(line) >= 78 && line[1:1]!="("
                number = line[1:5]
                op = line[7:7]
                type = line[8:8]
                name = line[11:22]
                volt = line[25:28]
                phase = line[29:32]
                must = line[33:37]
                uf = line[74:76]
                ss = line[77:78]
                push!(col_number, number)
                push!(col_op, op)
                push!(col_type, type)
                push!(col_name, name)
                push!(col_volt, volt)
                push!(col_phase, phase)
                push!(col_must, must)
                push!(col_uf, uf)
                push!(col_ss, ss)
                push!(col_cycle, cycles[cycle][1:4])
                push!(col_source, source[cycle])
            end
        end

        df_dc = DataFrame(NUMBER = col_number, OP = col_op, TYPE = col_type, NAME = col_name, VOLT = col_volt, PHASE = col_phase, MUST = col_must, UF = col_uf, SS = col_ss, CYCLE = col_cycle, SOURCE = col_source)
        csv_path = joinpath(tust_path, "dc_" * cycles[cycle] * ".csv")
        CSV.write(csv_path, df_dc)

        first_line_index = 0
        for i in 2:length(aneel_lines)
            line = aneel_lines[i]
            if line[1:4] == "DLIN"
                first_line_index = i
                break
            end
        end
        first_line_index

        final_line_index = 0
        for i in first_line_index:length(aneel_lines)
            line = aneel_lines[i]
            if length(line)>= 5 && line[1:5] == "99999"
                final_line_index = i
                break
            end
        end
        final_line_index

        col_de = []    
        col_nome_de = [] 
        col_para = []
        col_nome_para = []
        col_circ = []
        col_est = []

        for i in first_line_index+2:final_line_index-2
            line = aneel_lines[i]
            if length(line) >= 20 && line[1:1]!="("
                de = line[1:5]
                index = findfirst(isequal(de), df_dc[:,"NUMBER"])
                if index === nothing
                    nome_de = ""
                else
                    nome_de = df_dc[index,"NAME"]
                end
                para = line[11:15]
                index = findfirst(isequal(para), df_dc[:,"NUMBER"])
                if index === nothing
                    nome_para = ""
                else
                    nome_para = df_dc[index,"NAME"]
                end
                circ = line[16:17]
                est = line[18:18]
                push!(col_de, de)
                push!(col_nome_de, nome_de)
                push!(col_de, para)
                push!(col_nome_de, nome_para)
                push!(col_para, para)
                push!(col_nome_para, nome_para)
                push!(col_para, de)
                push!(col_nome_para, nome_de)
                push!(col_circ, circ)
                push!(col_circ, circ)
                push!(col_est, est)
                push!(col_est, est)
            end
        end

        df_dlin = DataFrame(DE = col_de, NOME_DE = col_nome_de, PARA = col_para, NOME_PARA = col_nome_para, CIRC = col_circ, EST = col_est)
        csv_path = joinpath(tust_path, "dlin_" * cycles[cycle] * ".csv")
        CSV.write(csv_path, df_dlin)
    end
end

function convert_tuh(tust_path, cycles)
    for cycle in 1:length(cycles)
        aneel_example_path = joinpath(tust_path, cycles[cycle] * ".tuh")
        aneel_input = open(aneel_example_path,"r")
        aneel_lines = readlines(aneel_input)
        close(aneel_input)

        final_line_index = length(aneel_lines)

        col_name = []
        col_ceg = []
        col_tust = []
        col_cycle = []
        col_source = []
        for i in 12:final_line_index-2
            line = aneel_lines[i]
            name = rstrip(line[4:34])
            ceg = line[37:44]
            tust = line[127:132]
            push!(col_name, name)
            push!(col_ceg, ceg)
            push!(col_tust, tust)
            push!(col_cycle, cycles[cycle][1:4])
            push!(col_source, source[cycle])
        end

        df_tuh = DataFrame(CEG = col_ceg, NAME = col_name, TUST = col_tust, CYCLE = col_cycle, SOURCE = col_source)
        csv_path = joinpath(tust_path, "tuh_" * cycles[cycle] * ".csv")
        CSV.write(csv_path, df_tuh)
    end
end

function convert_nos(tust_path, cycles)
    for cycle in 1:length(cycles)
        aneel_example_path = joinpath(tust_path, cycles[cycle] * ".nos")
        aneel_input = open(aneel_example_path,"r")
        aneel_lines = readlines(aneel_input)
        close(aneel_input)

        final_line_index = length(aneel_lines)-8

        col_number = []
        col_name = []
        col_tustb = []
        col_cycle = []
        col_source = []

        for i in 13:final_line_index-2
            line = aneel_lines[i]
            number = line[3:7]
            name = line[9:20]
            tustb = line[35:43]
            push!(col_number, number)
            push!(col_name, name)
            push!(col_tustb, tustb)
            push!(col_cycle, cycles[cycle][1:4])
            push!(col_source, source[cycle])
        end

        df_nos = DataFrame(NUMBER = col_number, NAME = col_name, TUSTB = col_tustb, CYCLE = col_cycle, SOURCE = col_source)
        csv_path = joinpath(tust_path, "nos_" * cycles[cycle] * ".csv")
        CSV.write(csv_path, df_nos)
    end
end