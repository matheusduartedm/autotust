import os
import csv
import subprocess
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from collections import defaultdict


class Generator:
    def __init__(self):
        self.type = ""
        self.name = ""
        self.must = {}
        self.s = {}
        self.d = {}
        self.ceg = ""
        self.cegnucleo = 0
        self.bus = {}
        self.tust = {}
        self.uf = ""

    def set_tust(self, year, value):
        self.tust[year] = value

    def get_tust(self, year):
        return self.tust.get(year)


class Bus:
    def __init__(self):
        self.num = 0
        self.name = ""
        self.area = 0
        self.circuits = {}


def _is_comment(line):
    return len(line) <= 1 or line[0] == "("


def _is_end_of_file(line):
    return line[:2].strip() == "X"


def _load_r61_data(r61_file):
    data = {}
    with open(r61_file, 'r', encoding='ISO-8859-1') as file:
        lines = file.readlines()
        # Extract rap
        rap_total_str = lines[7][88:106].replace(".", "").replace(",", ".")
        data["rap"] = float(rap_total_str) if rap_total_str.strip() not in ["", "------"] else None
        # Extract mustg
        must_ger_str = lines[8][15:26].replace(".", "").replace(",", ".")
        data["mustg"] = float(must_ger_str) if must_ger_str.strip() not in ["", "------"] else None
        # Extract mustp
        must_cp_str = lines[8][55:66].replace(".", "").replace(",", ".")
        data["mustp"] = float(must_cp_str) if must_cp_str.strip() not in ["", "------"] else None
        # Extract mustfp
        must_fp_str = lines[8][75:86].replace(".", "").replace(",", ".")
        data["mustfp"] = float(must_fp_str) if must_fp_str.strip() not in ["", "------"] else None
        # Extract TEU
        teu_values = []
        for i in range(17, 20):
            if i < len(lines):
                teu_str = lines[i][7:14].replace(",", ".")
                teu_values.append(float(teu_str) if teu_str.strip().strip('-') != "" else None)

            else:
                teu_values.append(None)

        if len(lines) < 20:
            teu_values.append(None)
        data["teug"] = teu_values[0]
        data["teup"] = teu_values[1]
        data["teufp"] = teu_values[2]

    return data


def load_dc(DB_PATH, year):
    dc_file = DB_PATH + f"\\{year}-{year+1}.DC"
    
    if os.path.exists(dc_file):
        buses = {}
        found_dbar = False
        found_dlin = False
        
        with open(dc_file, "r") as file:
            for line in file:
                stripped_line = line.strip()

                if stripped_line == "DBAR":
                    found_dbar = True
                    continue
                
                elif stripped_line == "DLIN":
                    found_dlin = True
                    continue
                
                if stripped_line == "99999":
                    found_dbar = found_dlin = False
                
                if not found_dbar and not found_dlin:
                    continue
                
                if _is_comment(line):
                    continue

                if len(stripped_line) > 0:
                    if found_dbar:
                        bus = Bus()
                        bus.num = int(line[0:5].strip())
                        bus.name = line[10:22].strip()
                        bus.area = int(line[76:78].strip())
                        buses[bus.num] = bus
                    elif found_dlin:
                        from_bus = int(line[0:5].strip())
                        to_bus = int(line[10:15].strip())
                        
                        if from_bus in buses:
                            if year not in buses[from_bus].circuits:
                                buses[from_bus].circuits[year] = []
                            if to_bus not in buses[from_bus].circuits[year]:
                                buses[from_bus].circuits[year].append(to_bus)
                        
                        if to_bus in buses:
                            if year not in buses[to_bus].circuits:
                                buses[to_bus].circuits[year] = []
                            if from_bus not in buses[to_bus].circuits[year]:
                                buses[to_bus].circuits[year].append(from_bus)

        return buses


def load_ger(DB_PATH, year):
    ger_file = DB_PATH + f"\\{year}-{year+1}.GER"
    if os.path.exists(ger_file):
        generators = {}
        duplicated_generators = {}
        with open(ger_file, "r") as file:
            for line in file:
                if _is_comment(line):
                    continue

                if len(line) > 0:
                    name = line[0:32].strip()
                    generator = Generator()
                    generator.name = name
                    generator.type = name[0:3]
                    generator.ceg = line[52:62].strip()
                    if generator.ceg[-7:][:5].strip():
                        generator.cegnucleo = int(generator.ceg[-7:][:5]) if generator.ceg[-7:][:5].isdigit() else generator.ceg[-7:][:5]

                    if name not in generators:
                        generators[name] = generator
                    else:
                        if name not in duplicated_generators:
                            duplicated_generators[name] = [generators[name]]

                    generator.d[year] = line[42:43].strip()
                    generator.s[year] = line[44:45].strip()
                    generator.must[year] = float(line[32:41].strip())
                    generator.bus[year] = int(line[70:75].strip())

        return generators, duplicated_generators


def load_base(DB_PATH):
    generators = {}
    r61_data = {
        "rap": {},
        "mustg": {},
        "mustp": {},
        "mustfp": {},
        "teug": {},
        "teup": {},
        "teufp": {},
    }
    years = range(2022, 2032)
    for year in years:
        ger_file = DB_PATH + f"\\{year}-{year+1}.GER"
        tuh_file = DB_PATH + f"\\{year}-{year+1}.TUH"
        r61_file = DB_PATH + f"\\{year}-{year+1}.R61"

        if os.path.exists(ger_file):
            with open(ger_file, "r") as file:
                for line in file:
                    if _is_comment(line):
                        continue

                    if len(line) > 0:
                        name = line[0:32].strip()
                        if len(line) > 0:
                            name = line[0:32].strip()
                            if name not in generators:
                                generator = Generator()
                                generator.name = name
                                generator.type = name[0:3]
                                generator.ceg = line[52:62].strip()
                                if generator.ceg[-7:][:5].strip():
                                    generator.cegnucleo = int(generator.ceg[-7:][:5]) if generator.ceg[-7:][:5].isdigit() else generator.ceg[-7:][:5]
                                generators[name] = generator
                            generators[name].d[year] = line[42:43].strip()
                            generators[name].s[year] = line[44:45].strip()
                            generators[name].must[year] = float(line[32:41].strip())
                            generators[name].bus[year] = int(line[70:75].strip())
                print(f"Geradores carregados para o ano {year}-{year+1}.")


        if os.path.exists(tuh_file):
            with open(tuh_file, "r") as file:
                line_number = 0

                for line in file:
                    line_number += 1

                    if line_number <= 11:
                        continue

                    if _is_comment(line):
                        continue

                    if _is_end_of_file(line):
                        break

                    if len(line) > 0:
                        name = line[3:35].strip()
                        tust = float(line[96:102])
                        uf = line[51:53].strip()
                        if name in generators:
                            generator = generators[name]
                            generators[name].tust[year] = tust
                            generators[name].uf = generators[name].uf if generators[name].uf else uf


                        else:
                            print(f"Gerador {name} não encontrado na lista de geradores.")

        # Load .R61 data
        if os.path.exists(r61_file):
            year_data = _load_r61_data(r61_file)
            for key in r61_data.keys():
                r61_data[key][year] = year_data[key]
    
    generators = sorted(generators.items(), key=lambda x: x[0])
    generators = dict(generators)

    # Adicionar anos extras para o dashboard
    extra_years = range(2032, 2040)
    for name in generators:
        generator = generators[name]
        for year in extra_years:
            generator.tust[year] = generator.tust.get(year-1, 0) - 0.02

    combined_years = list(years) + list(extra_years)

    # Criar o arquivo CSV
    csv_file = DB_PATH + "\\" + "autotust_list.csv"
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["GENERATOR"] + [str(year) for year in combined_years]
        writer.writerow(header)

        for name, generator in generators.items():
            row = [name]
            for year in combined_years:
                tust = generator.tust.get(year, 0)
                row.extend([tust])
            writer.writerow(row)
            
    return generators, r61_data


def create_dashboard():
    BASE_DIR = r"bases"
    base_options = [name for name in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, name))]
    base_selection = st.sidebar.selectbox("Select case:", base_options)
    CASE_PATH = os.path.join(BASE_DIR, base_selection)

    generators, r61_data = load_base(CASE_PATH)

    ss = {
        'AP': 'N', 'AM': 'N', 'PA': 'N', 'RR': 'N', 'TO': 'N','MA': 'N', 
        'AL': 'NE', 'BA': 'NE', 'CE': 'NE', 'PB': 'NE', 'PE': 'NE', 'PI': 'NE', 'RN': 'NE', 'SE': 'NE',
        'ES': 'SE', 'MG': 'SE', 'RJ': 'SE', 'SP': 'SE', 'GO': 'SE', 'MS': 'SE', 'MT': 'SE', 'DF': 'SE', 'AC': 'SE', 'RO': 'SE',
        'PR': 'S', 'RS': 'S', 'SC': 'S'
    }

    # Sidebar
    st.sidebar.title("Navigation")
    tab_names = ["General Results", "Assumptions", "Results"]
    tab = st.sidebar.radio("", tab_names)
    generator_ids = list(generators.keys())

    if tab == "General Results":
        st.write("# General Results")
        
        total_tust_by_ss = defaultdict(lambda: defaultdict(float))
        generator_count_by_ss = defaultdict(int)
        
        # Calculando o total de TUST e contagem de geradores por subsistema
        for generator in generators.values():
            subsistema = ss.get(generator.uf, '')
            generator_count_by_ss[subsistema] += 1
            for year, tust in generator.tust.items():
                total_tust_by_ss[subsistema][year] += tust
        
        # Exibindo os totais de TUST por subsistema
        st.write("## Totais de TUST por Subsistema")
        for subsistema, tusts in total_tust_by_ss.items():
            st.write(f"Subsistema: {subsistema}")
            for year, value in tusts.items():
                st.write(f"Ano: {year}, Total TUST: {value}")
        
        # Calculando e exibindo a média de TUST por subsistema
        avg_tust_by_ss = {}
        for subsistema, tusts in total_tust_by_ss.items():
            avg_tust_by_ss[subsistema] = {year: value / generator_count_by_ss[subsistema] for year, value in tusts.items()}
        
        fig = go.Figure()
        for subsistema, avg_tusts in avg_tust_by_ss.items():
            years = list(avg_tusts.keys())
            values = list(avg_tusts.values())
            fig.add_trace(go.Scatter(x=years, y=values, mode='markers+lines', name=subsistema))
        
        fig.update_layout(title="TUST Média por Subsistema", xaxis_title='Ano', yaxis_title='TUST Média [R$/kW.month - ref. Jun/2023]')
        st.plotly_chart(fig)


    elif tab == "Results":
        st.write("# Results")
        generator_id = st.selectbox("Select the generator: ", generator_ids)
        if generator_id in generators:
            generator = generators[generator_id]

            years = list(generator.tust.keys())
            tust_values = list(generator.tust.values())
            years = [int(year) for year in years]  # Convert years to integers

            # Calculate the average of tust_values for the specific generator
            average_generator = np.mean(tust_values)
            average_generator_line = [average_generator] * len(years)

            # Calculate the global average of all generators
            all_tust_values = []
            for g in generators.values():
                all_tust_values.extend(list(g.tust.values()))
            average_global = np.mean(all_tust_values)
            average_global_line = [average_global] * len(years)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=years, y=tust_values, mode='markers+lines', name='TUST'))
            fig.add_trace(go.Scatter(x=years, y=average_generator_line, mode='lines', name='Average (Generator)'))
            fig.add_trace(go.Scatter(x=years, y=average_global_line, mode='lines', name='Average (Global)'))

            fig.update_layout(title=f"TUST per Tariff Cycle for {generator_id}", xaxis_title='Tariff Cycle', yaxis_title='TUST [R$/kW.month - ref. Jun/2023]')
            st.plotly_chart(fig)

            # Calculate the nominal TUST
            iat = st.number_input("Enter the value of IAT (%):", value=4.0, step=0.5)
            risk_expansion = st.number_input("Enter the value of Risk Expansion (%):", value=5.0, step=0.5)
            limit = iat + risk_expansion  # define limit

            cumulative_iat = 1 + (iat / 100)
            tust_nominal_values = []
            controlled_tust = []
            limit_upper_values = []
            limit_lower_values = []

            for i, year in enumerate(years):
                cumulative_iat *= (1 + (iat / 100))
                tust_nominal = generator.tust[year] * cumulative_iat
                tust_nominal_values.append(tust_nominal)

                if i == 0:  # for the first year
                    controlled_tust.append(tust_nominal)
                    limit_upper_values.append(tust_nominal)
                    limit_lower_values.append(tust_nominal)
                else:  # for subsequent years
                    controlled_tust_prev = controlled_tust[i-1]
                    limit_upper = (controlled_tust_prev * 0.8 + tust_nominal * 0.2) * (1 + limit / 100)
                    limit_lower = (controlled_tust_prev * 0.8 + tust_nominal * 0.2) * (1 - limit / 100)
                    limit_upper_values.append(limit_upper)
                    limit_lower_values.append(limit_lower)

                    # The controlled_tust for the current year will be between the upper and lower limits
                    controlled_tust_current = max(min(tust_nominal, limit_upper), limit_lower)
                    controlled_tust.append(controlled_tust_current)

            fig_nominal = go.Figure()
            fig_nominal.add_trace(go.Scatter(x=years, y=limit_upper_values, mode='lines', name='Upper Limit', line=dict(width=0)))
            fig_nominal.add_trace(go.Scatter(x=years, y=limit_lower_values, mode='lines', name='Lower Limit', line=dict(width=0), fill='tonexty'))
            fig_nominal.add_trace(go.Scatter(x=years, y=tust_nominal_values, mode='markers+lines', name='TUST Nominal'))
            fig_nominal.add_trace(go.Scatter(x=years, y=controlled_tust, mode='markers+lines', name='TUST Controlled'))
            fig_nominal.update_layout(title=f"TUST Nominal per Tariff Cycle for {generator_id} (IAT = {iat}%)", xaxis_title='Tariff Cycle', yaxis_title='TUST Nominal [R$/kW.month - ref. Jun/Cycle]')
            st.plotly_chart(fig_nominal)

            # Create a download button for the selected generator
            data = pd.DataFrame.from_dict(generator.tust, orient='index', columns=['TUST'])
            data.index.name = 'Year'
            csv = data.to_csv().encode()
            st.download_button(label="Download generator data", data=csv, file_name=f"{generator_id}_tust_data.csv", mime="text/csv")

            # Create a download button for all generators
            all_data = pd.concat([pd.DataFrame.from_dict(g.tust, orient='index', columns=['TUST']).assign(Generator_id=gid) for gid, g in generators.items()])
            all_data.index.name = 'Year'
            all_csv = all_data.to_csv().encode()
            st.download_button(label="Download all data", data=all_csv, file_name="all_tust_data.csv", mime="text/csv")

        else:
            st.write(f"Generator {generator_id} not found.")
    

    elif tab == "Assumptions":
        st.write("# Assumptions")
        st.write("### GER File")

        if generators.values():
            # Get the list of years
            must_total_years = list(generators.values())[0].must.keys()
            
            # Create a dictionary to store MUST values by type
            must_values_by_type = defaultdict(lambda: defaultdict(int))

            # Iterate over all generators and add MUST values to the corresponding type and year
            for generator in generators.values():
                for year in must_total_years:
                    must_values_by_type[generator.type][year] += generator.must.get(year, 0)

            # Calculate the total MUST values for each year
            must_total_values = {year: sum(values[year] for values in must_values_by_type.values()) for year in must_total_years}

            # Get the list of types in reverse sorted order
            types_sorted = sorted(must_values_by_type.keys(), reverse=True)  # Reverse order

            # Plot a separate bar for each type
            fig_must_total = go.Figure()
            for type_ in types_sorted:
                must_values = must_values_by_type[type_]
                fig_must_total.add_trace(go.Bar(
                    x=list(must_total_years),
                    y=[value / 1e3 for value in must_values.values()],  # Convert to GW
                    text=[f"{float(value/1e3):4.2f} GW" for value in must_values.values()],
                    textposition='inside',
                    name=type_
                ))

            # Add total values as a separate trace
            fig_must_total.add_trace(go.Scatter(
                x=list(must_total_years),
                y=[value / 1e3 for value in must_total_values.values()],  # Convert to GW
                mode='text',
                text=[f"{float(value/1e3):4.2f} GW" for value in must_total_values.values()],
                textposition='top center',
                showlegend=False  # Do not show this trace in the legend
            ))

            fig_must_total.update_layout(
                title="MUST by Year",
                xaxis_title="<b>Year</b>",
                xaxis=dict(
                    tickmode='linear',
                    dtick=1
                ),
                title_x=0.5,
                barmode='stack'  # Stack bars for different types
            )
            fig_must_total.update_yaxes(visible=False)
            st.plotly_chart(fig_must_total)

        else:
            st.write("O dicionário 'generators' está vazio.")

        st.write("### R61 File")
        # Display the RAP data
        rap_years = list(r61_data["rap"].keys())
        rap_values = list(r61_data["rap"].values())

        fig_rap = go.Figure(data=[go.Bar(x=rap_years, y=rap_values, 
                                        text=[f"{float(value/1e9):4.2f} B" for value in rap_values],
                                        textposition='outside')])
        fig_rap.update_layout(title="RAP by Year", xaxis_title="<b>Year</b>", title_x=0.5, 
                            xaxis=dict(tickmode='linear', dtick=1))
        fig_rap.update_yaxes(visible=False)
        st.plotly_chart(fig_rap)

        # Display the MUST data
        must_years = list(r61_data["mustg"].keys())
        must_ger_values = list(r61_data["mustg"].values())
        must_cp_values = list(r61_data["mustp"].values())
        must_fp_values = list(r61_data["mustfp"].values())

        fig_must = go.Figure(data=[go.Bar(x=must_years, y=must_ger_values,
                                        text=[f"{float(value/1e3):4.2f} GW" for value in must_ger_values],
                                        textposition='outside')])
        fig_must.update_layout(title="MUSTg by Year", xaxis_title="<b>Year</b>", title_x=0.5, 
                            xaxis=dict(tickmode='linear', dtick=1))
        fig_must.update_yaxes(visible=False)
        st.plotly_chart(fig_must)
        
        fig_must = go.Figure()
        fig_must.add_trace(go.Bar(x=must_years, y=must_cp_values, name="P",
                                text=[f"{float(value/1e3):4.1f}" if value is not None else 0 for value in must_cp_values],
                                textposition='outside'))
        fig_must.add_trace(go.Bar(x=must_years, y=must_fp_values, name="FP",
                                text=[f"{float(value/1e3):4.1f}" if value is not None else 0 for value in must_fp_values],
                                textposition='outside'))
        fig_must.update_layout(title="MUSTc by Year", xaxis_title="<b>Year</b>", title_x=0.5, 
                            xaxis=dict(tickmode='linear', dtick=1))
        fig_must.update_yaxes(visible=False)
        st.plotly_chart(fig_must)


        # Display the TEU data
        teu_years = list(r61_data["teug"].keys())
        teu_g_values = list(r61_data["teug"].values())
        teu_cp_values = list(r61_data["teup"].values())
        teu_cf_values = list(r61_data["teufp"].values())

        fig_teu = go.Figure(data=[go.Bar(x=teu_years, y=teu_g_values,
                                        text=[f"{value:3.2f}" for value in teu_g_values],
                                        textposition='outside')])
        fig_teu.update_layout(title="TEUg by Year", xaxis_title="<b>Year</b>", title_x=0.5, 
                            xaxis=dict(tickmode='linear', dtick=1))
        fig_teu.update_yaxes(visible=False)
        st.plotly_chart(fig_teu)

        fig_teu = go.Figure()
        fig_teu.add_trace(go.Bar(x=teu_years, y=teu_cp_values, name="P",
                                text=[f"{value:3.2f}" if value is not None else 0 for value in teu_cp_values],
                                textposition='outside'))
        fig_teu.add_trace(go.Bar(x=teu_years, y=teu_cf_values, name="FP",
                                text=[f"{value:3.2f}" if value is not None else 0 for value in teu_cf_values],
                                textposition='outside'))
        fig_teu.update_layout(title="TEUc by Year", xaxis_title="<b>Year</b>", title_x=0.5, 
                            xaxis=dict(tickmode='linear', dtick=1))
        fig_teu.update_yaxes(visible=False)
        st.plotly_chart(fig_teu)
   

def _read_param61(file_path):
    param_list = []
    if os.path.exists(file_path):
        with open(file_path) as param_file:
            for iline, line in enumerate(param_file):
                contents = line if (iline <= 3 or line == "\n") else float(line)
                param_list.append(contents)
    print(param_list)
    return param_list


def _write_param61(params, file_path):
	with open(file_path, "w") as param_file:
		for iparam, value in enumerate(params):
			if iparam == 0:
				param_file.write(f"{value}")
			elif 1 <= iparam <= 3:
				param_file.write(f"{value}\n")
			elif iparam == 4:
				param_file.write(f"{value:013.2f}\n")
			elif iparam == 5:
				param_file.write(f"{value}")
			elif 6 <= iparam <= 10:
				param_file.write(f"{value:05.1f}\n")
			elif iparam <= 11:
				param_file.write(f"{value:013.2f}\n")
			else:
				param_file.write(f"{value:05.2f}\n")


""" def create_param_file(file_path, case_path, cycle):
	params = []
	params.append(os.path.join(case_path, cycle + ".dc"))
	params.append(os.path.join(case_path, cycle))
	# ...
	_write_param(params, file_path) """


def run_nodal61(case_path, 
                rap = [41244217.19, 42551207.39, 43105639.57, 46475182.88, 46449217.35, 47993366.19, 48134649.99, 48204543.25], 
                pdr = [80, 70, 60, 50, 50, 50, 50, 50]):
    NODAL_PATH = r"C:\Program Files (x86)\Nodal_V61"
    cycle_begin = 2024
    cycle_end = 2032
    working_path = NODAL_PATH
    params_file_path = os.path.join(NODAL_PATH, "param.v61")
    
    """ 	if not os.exists(params_file_path):
        create_param_file(params_file_path, case_path, cycle_begin) """

    params = _read_param61(params_file_path)
    params[1] = NODAL_PATH
    for i, icycle in enumerate(range(cycle_begin, cycle_end)):
        cycle = f"{icycle}-{icycle+1}"
        params[2] = case_path + f"\{cycle}.dc"
        params[3] = case_path + f"\{cycle}"
        params[4] = rap[i]
        params[20] = pdr[i]
        _write_param61(params, params_file_path)
        command = "Nodal_F61.exe"
        subprocess.run(command, check=True, shell=True, cwd=NODAL_PATH)

        log_path = os.path.join(NODAL_PATH, "#ER_nod#.TX1")		
        if os.path.exists(log_path):
            with open(log_path, "r") as file:
                file_content = file.read()
                print(file_content)
        else:
            print("O arquivo #ER_nod#.TX1 não foi encontrado.")