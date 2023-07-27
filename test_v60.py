import autotust_v60

#SEMPRE RODAR O SCRIPT COMO ADMINISTRADOR

CASE_PATH = r"D:\dev\auto_tust\tests\BaseONS"

rap22 = [34878790.43, 40271940.87, 41069253.80, 42026676.05, 42533399.85, 46770103.61, 43872400.04, 45880764.06, 46073219.29]
pdr22 = [100, 90, 80, 70, 60, 50, 50, 50, 50]

#autotust_v60.run_nodal61(CASE_PATH, rap23, pdr23)

generators, r60_data = autotust_v60.load_base(CASE_PATH)

autotust_v60.create_dashboard(generators, r60_data)