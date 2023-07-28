import autotust_v61

CASE_PATH = r"BaseEPE"

generators, r61_data = autotust_v61.load_base(CASE_PATH)

autotust_v61.create_dashboard(generators, r61_data)