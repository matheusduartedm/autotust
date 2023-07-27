import autotust_v61

#SEMPRE RODAR O SCRIPT COMO ADMINISTRADOR

CASE_PATH = r"D:\dev\auto_tust\tests\BaseEPE"

rap23 = [41244217.19, 42551207.39, 43105639.57, 46475182.88, 46449217.35, 47993366.19, 48134649.99, 48204543.25]
pdr23 = [80, 70, 60, 50, 50, 50, 50, 50]

#autotust_v61.run_nodal61(CASE_PATH, rap23, pdr23)

generators, r61_data = autotust_v61.load_base(CASE_PATH)

autotust_v61.create_dashboard(generators, r61_data)