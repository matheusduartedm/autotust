import os
import sys
import colorsys
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import autotust

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@st.cache_data
def load_database(base_path):
    """Load the database from the given path."""
    return autotust.load_base(base_path)

def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)

def calculate_color(value, min_val, max_val):
    """Calculate color based on the normalized value."""
    norm_value = normalize(value, min_val, max_val)
    r, g, b = colorsys.hsv_to_rgb(0.3 * (1 - norm_value), 1, 1)
    return f"rgb({int(r * 255)},{int(g * 255)},{int(b * 255)})"

def create_line_chart(data, title, x_label, y_label):
    """Create a line chart with the given data and labels."""
    fig = go.Figure()
    for name, values in data.items():
        years, y_values = zip(*sorted(values.items()))
        fig.add_trace(go.Scatter(
            x=years, y=y_values, mode='markers+lines+text',
            text=[f"{value:.2f}" for value in y_values],
            textposition='top right', name=name
        ))
    fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label)
    return fig

def create_bar_chart(x_data, y_data, title, x_label, text=None, color=None):
    """Create a bar chart with the given data and labels."""
    fig = go.Figure(data=[go.Bar(x=x_data, y=y_data, text=text, textposition='outside', marker_color=color)])
    fig.update_layout(title=title, xaxis_title=x_label, title_x=0.5, xaxis=dict(tickmode='linear', dtick=1))
    fig.update_yaxes(visible=False)
    return fig


def display_results(database):
    """Display the results tab."""
    st.write("# Results")
    generator_id = st.selectbox("Select the generator:", [gen.name for gen in database.generators])
    generator = database.get_generator_by_name(generator_id)

    if generator:
        plot_generator_tust(generator, database.generators)
        plot_iat_and_risk_expansion(generator)
        st.download_button(
            label="Download generator data",
            data=convert_to_csv({generator_id: generator.tust}),
            file_name=f"{generator_id}_tust_data.csv",
            mime="text/csv"
        )
        all_data_csv = convert_to_csv({gen.name: gen.tust for gen in database.generators})
        st.download_button(
            label="Download all data",
            data=all_data_csv,
            file_name="all_tust_data.csv",
            mime="text/csv"
        )
    else:
        st.write(f"Generator {generator_id} not found.")

def plot_generator_tust(generator, all_generators):
    """Plot TUST values for the selected generator."""
    years, tust_values = zip(*generator.tust.items())
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years, y=tust_values, mode='markers+lines+text',
        text=[f"{value:.2f}" for value in tust_values],
        textposition='top center', name='TUST'
    ))

    average_generator = np.mean(tust_values)
    fig.add_trace(go.Scatter(
        x=years, y=[average_generator] * len(years),
        mode='lines', name='Average (Generator)'
    ))

    all_tust_values = [tust for gen in all_generators for tust in gen.tust.values()]
    average_global = np.mean(all_tust_values)
    fig.add_trace(go.Scatter(
        x=years, y=[average_global] * len(years),
        mode='lines', name='Average (Global)'
    ))

    fig.update_layout(
        title=f"TUST per Tariff Cycle for {generator.name}",
        xaxis_title='Tariff Cycle',
        yaxis_title='TUST [R$/kW.month - ref. Jun/2023]'
    )
    st.plotly_chart(fig)

def plot_iat_and_risk_expansion(generator):
    """Plot IAT and Risk Expansion for the selected generator."""
    iat = st.number_input("Enter the value of IAT (%):", value=4.0, step=0.5)
    risk_expansion = st.number_input("Enter the value of Risk Expansion (%):", value=5.0, step=0.5)
    limit = iat + risk_expansion

    cumulative_iat = 1 + (iat / 100)
    tust_nominal_values, controlled_tust, limit_upper_values, limit_lower_values = [], [], [], []

    years = list(generator.tust.keys())

    for i, year in enumerate(years):
        cumulative_iat *= (1 + (iat / 100))
        tust_nominal = generator.tust[year] * cumulative_iat
        tust_nominal_values.append(tust_nominal)

        if i == 0:
            controlled_tust.append(tust_nominal)
            limit_upper_values.append(tust_nominal)
            limit_lower_values.append(tust_nominal)
        else:
            prev_controlled_tust = controlled_tust[-1]
            limit_upper = (prev_controlled_tust * 0.8 + tust_nominal * 0.2) * (1 + limit / 100)
            limit_lower = (prev_controlled_tust * 0.8 + tust_nominal * 0.2) * (1 - limit / 100)
            limit_upper_values.append(limit_upper)
            limit_lower_values.append(limit_lower)

            controlled_tust.append(max(min(tust_nominal, limit_upper), limit_lower))

    fig_nominal = go.Figure()
    fig_nominal.add_trace(go.Scatter(
        x=years, y=limit_upper_values, mode='lines', name='Upper Limit',
        line=dict(width=0), fill=None
    ))
    fig_nominal.add_trace(go.Scatter(
        x=years, y=limit_lower_values, mode='lines', name='Lower Limit',
        line=dict(width=0), fill='tonexty'
    ))
    fig_nominal.add_trace(go.Scatter(
        x=years, y=tust_nominal_values, mode='markers+lines', name='TUST Nominal'
    ))
    fig_nominal.add_trace(go.Scatter(
        x=years, y=controlled_tust, mode='markers+lines+text',
        textposition='top center', text=[f"{value:.2f}" for value in tust_nominal_values],
        name='TUST Controlled'
    ))

    fig_nominal.update_layout(
        title=f"TUST Nominal per Tariff Cycle for {generator.name} (IAT = {iat}%)",
        xaxis_title='Tariff Cycle',
        yaxis_title='TUST Nominal [R$/kW.month - ref. Jun/Cycle]'
    )
    st.plotly_chart(fig_nominal)

def convert_to_csv(data_dict):
    """Convert the given data dictionary to a CSV."""
    df = pd.DataFrame.from_dict(data_dict, orient='index')
    df.index.name = 'Year'
    return df.to_csv().encode()

def display_general_results(database):
    """Display the general results tab."""
    st.write("# General Results")
    avg_tust = database.calculate_avg_tust()

    subsystem_data = {ss: tusts for ss, tusts in avg_tust.items() if ss in autotust.SUBSYSTEM_MAP.keys()}
    st.plotly_chart(create_line_chart(subsystem_data, "Average TUST by Subsystem", 'Year',
                                      'Average TUST [R$/kW.month - ref. Jun/2023]'))

    uf_data = {uf: tusts for uf, tusts in avg_tust.items() if uf in autotust.STATE_TO_SUBSYSTEM.keys()}
    st.plotly_chart(
        create_line_chart(uf_data, "Average TUST by UF", 'Year', 'Average TUST [R$/kW.month - ref. Jun/2023]'))

    type_data = {type_: tusts for type_, tusts in avg_tust.items() if
                 type_ not in autotust.SUBSYSTEM_MAP and type_ not in autotust.STATE_TO_SUBSYSTEM}
    st.plotly_chart(
        create_line_chart(type_data, "Average TUST by Type", 'Year', 'Average TUST [R$/kW.month - ref. Jun/2023]'))

def display_assumptions(database):
    """Display the assumptions tab."""
    st.write("# Assumptions")
    st.write("### GER File")

    if database.generators:
        must_values_by_type, must_total_values = database.calculate_must_values()
        must_total_years = list(must_values_by_type[next(iter(must_values_by_type))].keys())

        fig_must_total = go.Figure()
        for type_, must_values in sorted(must_values_by_type.items(), reverse=True):
            fig_must_total.add_trace(go.Bar(
                x=must_total_years, y=[value / 1e3 for value in must_values.values()],
                text=[f"{value / 1e3:.2f} GW" for value in must_values.values()],
                textposition='inside', name=type_
            ))

        fig_must_total.add_trace(go.Scatter(
            x=must_total_years, y=[value / 1e3 for value in must_total_values.values()],
            mode='text', text=[f"{value / 1e3:.2f} GW" for value in must_total_values.values()],
            textposition='top center', showlegend=False
        ))

        fig_must_total.update_layout(
            title="MUST by Year", xaxis_title="<b>Year</b>", xaxis=dict(tickmode='linear', dtick=1), title_x=0.5,
            barmode='stack'
        )
        fig_must_total.update_yaxes(visible=False)
        st.plotly_chart(fig_must_total)

    else:
        st.write("The 'generators' list is empty.")

    st.write("### Cycle Data")
    rap_years = [cycle_data.year for cycle_data in database.cycle_data]
    rap_values = [cycle_data.rap for cycle_data in database.cycle_data if cycle_data.rap is not None]

    st.plotly_chart(create_bar_chart(
        rap_years, rap_values, "RAP by Year", "<b>Year</b>",
        text=[f"{value / 1e9:.2f} B" for value in rap_values]
    ))

    must_ger_values = [cycle_data.mustg for cycle_data in database.cycle_data if cycle_data.mustg is not None]
    st.plotly_chart(create_bar_chart(
        rap_years, must_ger_values, "MUSTg by Year", "<b>Year</b>",
        text=[f"{value / 1e3:.2f} GW" for value in must_ger_values]
    ))

    must_cp_values = [cycle_data.mustp for cycle_data in database.cycle_data if cycle_data.mustp is not None]
    must_fp_values = [cycle_data.mustfp for cycle_data in database.cycle_data if cycle_data.mustfp is not None]

    st.plotly_chart(go.Figure([
        go.Bar(x=rap_years, y=must_cp_values, name="P",
               text=[f"{value / 1e3:.1f}" if value is not None else 0 for value in must_cp_values],
               textposition='outside'),
        go.Bar(x=rap_years, y=must_fp_values, name="FP",
               text=[f"{value / 1e3:.1f}" if value is not None else 0 for value in must_fp_values],
               textposition='outside')
    ]).update_layout(
        title="MUSTc by Year", xaxis_title="<b>Year</b>", title_x=0.5,
        xaxis=dict(tickmode='linear', dtick=1)
    ).update_yaxes(visible=False))

    teu_g_values = [cycle_data.teug for cycle_data in database.cycle_data if cycle_data.teug is not None]
    st.plotly_chart(create_bar_chart(
        rap_years, teu_g_values, "TEUg by Year", "<b>Year</b>",
        text=[f"{value:.2f}" for value in teu_g_values]
    ))

    teu_cp_values = [cycle_data.teup for cycle_data in database.cycle_data if cycle_data.teup is not None]
    teu_cf_values = [cycle_data.teufp for cycle_data in database.cycle_data if cycle_data.teufp is not None]

    st.plotly_chart(go.Figure([
        go.Bar(x=rap_years, y=teu_cp_values, name="P",
               text=[f"{value:.2f}" if value is not None else 0 for value in teu_cp_values], textposition='outside'),
        go.Bar(x=rap_years, y=teu_cf_values, name="FP",
               text=[f"{value:.2f}" if value is not None else 0 for value in teu_cf_values], textposition='outside')
    ]).update_layout(
        title="TEUc by Year", xaxis_title="<b>Year</b>", title_x=0.5,
        xaxis=dict(tickmode='linear', dtick=1)
    ).update_yaxes(visible=False))

def display_commands(base_path):
    """Display the commands tab."""
    st.write("# AutoTUST Commands")
    
    command = st.selectbox("Select command to run:", 
                           ["Run Nodal v62", "Generate TUST Results", "Clean GER Files"])
    
    if st.button("Execute Command"):
        if command == "Run Nodal v62":
            execute_autotust_command('nodal', base_path)
        elif command == "Generate TUST Results":
            execute_autotust_command('output', base_path)
        elif command == "Clean GER Files":
            execute_autotust_command('clean', base_path)

def execute_autotust_command(command, base_path):
    if command == 'nodal':
        csv_path = base_path / "autotust.csv"
        cycle_years, rap, pdr = autotust.read_autotust_csv(csv_path)
        autotust.run_nodal62(base_path, cycle_years, rap, pdr)
        st.success("Nodal v62 execution completed.")
    elif command == 'output':
        database = autotust.load_base(base_path)
        autotust.get_tust_results(base_path, database)
        st.success("TUST results generated.")
    elif command == 'clean':
        excel_path = st.text_input("Enter the path to the Excel file with generators to remove:")
        output_path = st.text_input("Enter the path to save the output CSV file:")
        if st.button("Run Clean Command"):
            if excel_path and output_path:
                autotust.clean_ger(excel_path, str(base_path), output_path)
                st.success("GER files cleaned and results saved.")
            else:
                st.warning("Please provide both Excel file path and output path.")

def gui():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="AutoTUST Dashboard", layout="wide")

    st.sidebar.title("Navigation")
    tab_names = ["Assumptions", "General Results", "Results", "Commands"]
    tab = st.sidebar.radio("", tab_names)

    # Allow the user to input the case path directly
    case_path = st.sidebar.text_input("Enter the case path:", value="./")
    BASE_PATH = Path(case_path)

    if not BASE_PATH.exists():
        st.error(f"The specified path {BASE_PATH} does not exist. Please check the path.")
        return

    try:
        database = load_database(BASE_PATH)
    except Exception as e:
        st.error(f"Error loading database: {str(e)}. Please ensure the specified path contains valid case files.")
        return

    if tab == "Results":
        display_results(database)
    elif tab == "General Results":
        display_general_results(database)
    elif tab == "Assumptions":
        display_assumptions(database)
    elif tab == "Commands":
        display_commands(BASE_PATH)

if __name__ == "__main__":
    gui()