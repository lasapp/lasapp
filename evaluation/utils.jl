
function split_models_into_files(filename)
    open(filename, "r") do f
        s = read(f, String)
    
        split_file = split(s, "@model")
        header = popfirst!(split_file)
        number_length = length(string(length(split_file)))
    
        for (i, model_str) in enumerate(split_file)
            number_str = lpad(string(i), number_length, "0")
            new_filename ="$(filename[1:end-3])_$number_str.jl"
            open(new_filename, "w") do f2
                print(f2, header * "@model" * model_str)
            end
        end
    end
    
end

filenames = [
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_02.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_04_1.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_04_2.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_04_3.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_05_1.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_05_2.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_05_3.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_06.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_07_1.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_07_2.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_08.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_09.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_11.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_12.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_13.jl",
    "evaluation/turing/statistical_rethinking_2/chapters/chapter_14.jl",
    "evaluation/turing/turing_tutorials/06_infinite-mixture-model.jl",
    "evaluation/turing/turing_tutorials/09_variational-inference.jl",
    "evaluation/turing/turing_tutorials/10_bayesian-differential-equations.jl",
    "evaluation/turing/turing_tutorials/11_probabilistic-pca.jl",
    "evaluation/turing/turing_tutorials/12_gplvm.jl",
]

for filename in filenames
    split_models_into_files(filename)
end

function strip_file_to_model_defs(header::String, filename)
    keep_lines = [header, "\nusing Turing\n"]
    n_models = 0

    open(filename, "r") do f
        s = read(f, String)
        lines = split(s, "\n")

        start_line = 0
        end_line = 0
        for (i, line) in enumerate(lines)
            if startswith(line, "@model")
                start_line = i
            end
            if startswith(line, "end") && start_line != 0
                end_line = i
                append!(keep_lines, lines[start_line:end_line])
                push!(keep_lines, "\n")
                start_line = 0
                end_line = 0
                n_models += 1
            end
        end
    end
    if end_line == 0 && start_line != 0
        @warn "Invalid model definition in $filename?"
    end
    if n_models == 0
        @warn "No model in $filename?"
    end

    open(filename, "w") do f
        write(f, join(keep_lines, "\n"))
    end
    return n_models
end

import JSON

function pymc()
    header = "# https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102"
    folder = "/Users/markus/Documents/pymc-resources/"

    chosen_subfolders = ["Bayes_Rules", "BDA3", "BCM/CaseStudies", "BCM/ModelSelection", "BCM/ParameterEstimation"]


    model_defs = []
    for sub_folder in chosen_subfolders
        for filename in readdir(folder * sub_folder; join=true)
            if endswith(filename, ".ipynb")
                short_filename = filename[length(folder)+1 : end]
                println(filename)
                file_header = header * "\n# " * short_filename * "\n\nimport pymc as pm\n\n" 
                # println(file_header)

                file_model_defs = []
                open(filename, "r") do f
                    j = JSON.parse(f)
                    for cell in j["cells"]
                        # .Model() can also be in output which we do not want
                        source = join(cell["source"])
                        if contains(source, "pm.Model()")
                            if count("pm.Model()", source) > 1
                                delim = "with pm.Model()"
                                for sub_source in split(source, delim)[2:end]
                                    push!(file_model_defs, file_header * delim * sub_source)
                                end
                                # println(source)
                            else
                                push!(file_model_defs, file_header * source)
                            end
                        end
                    end
                end
                number_length = length(string(length(file_model_defs)))
                for (i, model_def) in enumerate(file_model_defs)
                    number_str = lpad(string(i), number_length, "0")
                    push!(model_defs, (sub_folder, short_filename[1:end-6] * "_" * number_str * ".py", model_def))
                end
            end
        end
    end
    model_defs
end
model_defs = pymc();

write_folder = "evaluation/pymc/"
for (sub_folder, name, model_def) in model_defs
    mkpath(write_folder * sub_folder)
    println("\033[95m", write_folder*name, "\033[0m")
    # println(model_def)
    open(write_folder*name, "w") do f
        write(f, model_def)
    end
end


# stan extract programs with if in model block

begin
    c = 0
    for (root, dir, files) in walkdir("/Users/markus/Documents/stan-example-models/")
        if endswith(root, "! other")
            continue
        end
        for file in files
            if endswith(file, ".stan") || endswith(file, ".R")
                s = read(joinpath(root, file), String)
                if contains(s, r"functions\s*{")
                    continue
                end
                # println(root, " ", joinpath(root, file))
                # println(file, ": ", findall(r"model\s*\{", s))
                for (i,j) in findall(r"(^|\n)\s*model\s*\{", s)
                    k = i
                    while s[k] != '{'
                        k += 1
                    end
                    k2 = k
                    open = 1
                    closed = 0
                    while open > closed
                        k2 += 1
                        open += s[k2] == '{'
                        closed += s[k2] == '}'
                    end
                    model_block = s[k:k2]

                    # println(i, ", ", j, ": ", s[i:j], " ", s[k], " ", s[k2])
                    if contains(model_block, r"if\s+\(.+\)\s+\{")
                        contains(model_block, r"target\s*\+=") && continue
                        c += 1
                        println(joinpath(root, file))
                    end
                    # c += 1
                end
            end
        end
    end
    c 
end
# /Users/markus/Documents/stan-example-models/bugs_examples/vol3/fire/fire.stan


begin
    c = 0
    for (root, dir, files) in walkdir("/Users/markus/Documents/stan-example-models/ARM")
        for file in files
            if endswith(file, ".stan")
                println(file)
                s = read(joinpath(root, file), String)
                if contains(s, r"functions\s*{")
                    continue
                end
                if contains(s, r"target\s*\+=")
                    continue
                end

                println(file)
                c += 1
            end
        end
    end
    c
end

begin
    min_bytes = 2^31
    max_bytes = 0
    c = 0
    for (root, dir, files) in walkdir("/Users/markus/Documents/stan-example-models/")
        for file in files
            if endswith(file, ".stan")
                c += 1
                size = filesize(joinpath(root, file))
                if size > 0
                    # println(joinpath(root, file))
                    min_bytes = min(min_bytes, size)
                    max_bytes = max(max_bytes, size)
                end
            end
        end
    end
    c, min_bytes, max_bytes
end