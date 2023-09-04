import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import defaultdict
import autotust_v61 as autotust
import colorsys

BASE_DIR = r"bases"
base_options = [name for name in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, name))]
base_selection = st.sidebar.selectbox("Select case:", base_options)
BASE_PATH = os.path.join(BASE_DIR, base_selection)

generators, r61_data = autotust.load_base(BASE_PATH)

ss = {
    'AP': 'N', 'AM': 'N', 'PA': 'N', 'RR': 'N', 'TO': 'N','MA': 'N', 
    'AL': 'NE', 'BA': 'NE', 'CE': 'NE', 'PB': 'NE', 'PE': 'NE', 'PI': 'NE', 'RN': 'NE', 'SE': 'NE',
    'ES': 'SE', 'MG': 'SE', 'RJ': 'SE', 'SP': 'SE', 'GO': 'SE', 'MS': 'SE', 'MT': 'SE', 'DF': 'SE', 'AC': 'SE', 'RO': 'SE',
    'PR': 'S', 'RS': 'S', 'SC': 'S'
}

def calculate_color(value, min_val, max_val):
    norm_value = (value - min_val) / (max_val - min_val)
    r, g, b = colorsys.hsv_to_rgb(0.3 * (1 - norm_value), 1, 1)
    r = max(0, min(255, int(r*255)))
    g = max(0, min(255, int(g*255)))
    b = max(0, min(255, int(b*255)))
    return f"rgb({r},{g},{b})"

# Sidebar
st.sidebar.title("Navigation")
tab_names = ["Assumptions", "General Results", "Results"]
tab = st.sidebar.radio("", tab_names)
generator_ids = list(generators.keys())

if tab == "Results":
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

elif tab == "General Results":
    st.write("# General Results")
    
    total_tust_by_ss = defaultdict(lambda: defaultdict(float))
    generator_count_by_ss = defaultdict(lambda: defaultdict(int))
    
    total_tust_by_uf = defaultdict(lambda: defaultdict(float))
    generator_count_by_uf = defaultdict(lambda: defaultdict(int))
    
    total_tust_by_type = defaultdict(lambda: defaultdict(float))
    generator_count_by_type = defaultdict(lambda: defaultdict(int))

    for generator in generators.values():
        subsystem = ss.get(generator.uf, '')
        for year, tust in generator.tust.items():
            if tust > 0:
                total_tust_by_ss[subsystem][year] += tust
                generator_count_by_ss[subsystem][year] += 1
                total_tust_by_uf[generator.uf][year] += tust
                generator_count_by_uf[generator.uf][year] += 1
                total_tust_by_type[generator.type][year] += tust
                generator_count_by_type[generator.type][year] += 1

    avg_tust_by_ss = {}
    for subsystem, tusts in total_tust_by_ss.items():
        avg_tust_by_ss[subsystem] = {year: round(value / generator_count_by_ss[subsystem][year], 2) for year, value in tusts.items()}

    all_avg_values = [avg for sub_avg in avg_tust_by_ss.values() for avg in sub_avg.values()]
    min_avg_tust = min(all_avg_values)
    max_avg_tust = max(all_avg_values)
    color_mapping = {ss: calculate_color(sum(tusts.values())/len(tusts.values()), min_avg_tust, max_avg_tust) for ss, tusts in avg_tust_by_ss.items()}

    subsystem_order = sorted(avg_tust_by_ss.keys(), key=lambda x: -sum(avg_tust_by_ss[x].values()))

    fig_ss = go.Figure()
    for subsistema in subsystem_order:
        years, values = zip(*sorted(avg_tust_by_ss[subsistema].items()))
        text_values = [str(value) for value in values]
        fig_ss.add_trace(go.Scatter(x=years, y=values, mode='markers+lines+text', text=text_values, textposition='top right', name=subsistema, line=dict(color=color_mapping[subsistema])))

    fig_ss.update_layout(title="Average TUST by Subsystem", xaxis_title='Year', yaxis_title='Average TUST [R$/kW.month - ref. Jun/2023]')
    st.plotly_chart(fig_ss)

    avg_tust_by_uf = {}
    for uf, tusts in total_tust_by_uf.items():
        avg_tust_by_uf[uf] = {year: round(value / generator_count_by_uf[uf][year], 2) for year, value in tusts.items()}

    uf_order = sorted(avg_tust_by_uf.keys(), key=lambda x: -sum(avg_tust_by_uf[x].values()))

    fig_uf = go.Figure()
    for uf in uf_order:
        years, values = zip(*sorted(avg_tust_by_uf[uf].items()))
        fig_uf.add_trace(go.Scatter(x=years, y=values, mode='markers+lines', textposition='top right', name=uf, line=dict(color=calculate_color(sum(values)/len(values), min_avg_tust, max_avg_tust))))

    fig_uf.update_layout(title="Average TUST by UF", xaxis_title='Year', yaxis_title='Average TUST [R$/kW.month - ref. Jun/2023]')
    st.plotly_chart(fig_uf)

    avg_tust_by_type = {}
    for type_, tusts in total_tust_by_type.items():
        avg_tust_by_type[type_] = {year: round(value / generator_count_by_type[type_][year], 2) for year, value in tusts.items()}

    all_avg_values_type = [avg for type_avg in avg_tust_by_type.values() for avg in type_avg.values()]
    min_avg_tust_type = min(all_avg_values_type)
    max_avg_tust_type = max(all_avg_values_type)
    color_mapping_type = {type_: calculate_color(sum(tusts.values())/len(tusts.values()), min_avg_tust_type, max_avg_tust_type) for type_, tusts in avg_tust_by_type.items()}

    type_order = sorted(avg_tust_by_type.keys(), key=lambda x: -sum(avg_tust_by_type[x].values()))

    fig_type = go.Figure()
    for type_ in type_order:
        years, values = zip(*sorted(avg_tust_by_type[type_].items()))
        text_values = [str(value) for value in values]
        fig_type.add_trace(go.Scatter(x=years, y=values, mode='markers+lines+text', text=text_values, textposition='top right', name=type_, line=dict(color=color_mapping_type[type_])))

    fig_type.update_layout(title="Average TUST by Type", xaxis_title='Year', yaxis_title='Average TUST [R$/kW.month - ref. Jun/2023]')
    st.plotly_chart(fig_type)


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
            showlegend=False
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