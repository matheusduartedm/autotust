using CSV, DataFrames

study_path = raw"C:\Users\matheusduarte\Desktop\Teste\infos.csv"
study = CSV.read(study_path, DataFrame)

cycles = [
    "2022-2023", "2023-2024", "2024-2025", "2025-2026", "2026-2027",
    "2027-2028", "2028-2029", "2029-2030", "2030-2031"
]

df_tust = DataFrame(
    NOME = String[],
    TUST_22_23 = Float64[],
    TUST_23_24 = Float64[],
    TUST_24_25 = Float64[],
    TUST_25_26 = Float64[],
    TUST_26_27 = Float64[],
    TUST_27_28 = Float64[],
    TUST_28_29 = Float64[],
    TUST_29_30 = Float64[],
    TUST_30_31 = Float64[]
)

for plant in 1:length(study[:,1])
    name = study[plant, "NOME"]
    bus01_ons = study[plant, "BUS01_ONS"]
    bus01_epe = study[plant, "BUS01_EPE"]
    
    tust_dict = Dict{String, Float64}()
    
    for cycle in cycles
        tuh_path = joinpath(study[plant, "PATH"], "tuh_" * cycle * ".csv")
        tuh = CSV.read(tuh_path, DataFrame)
        
        if findfirst(tuh[:, "NAME"] .== name) != nothing
            line = findfirst(tuh[:, "NAME"] .== name)
            tust = tuh[line, "TUST"]
            tust_dict[cycle] = tust
        else
            nos_path = joinpath(study[plant, "PATH"], "nos_" * cycle * ".csv")
            nos = CSV.read(nos_path, DataFrame)
            if findfirst(nos[:, "NUMBER"] .== bus01_ons) != nothing
                line = findfirst(nos[:, "NUMBER"] .== bus01_ons)
            else
                line = findfirst(nos[:, "NUMBER"] .== bus01_epe)
            end            
            tust = nos[line, "TUSTB"]
            tust_dict[cycle] = parse(Float64, tust)
        end
    end
    
    push!(df_tust, [
        name,
        tust_dict["2022-2023"],
        tust_dict["2023-2024"],
        tust_dict["2024-2025"],
        tust_dict["2025-2026"],
        tust_dict["2026-2027"],
        tust_dict["2027-2028"],
        tust_dict["2028-2029"],
        tust_dict["2029-2030"],
        tust_dict["2030-2031"]
    ])
end

csv_path = joinpath(result_path, "tust.csv")
CSV.write(csv_path, df_tust)