
function count_lines_of_code_in_file(filename)
    c = 0
    open(filename, "r") do f
        for line in split(read(f,String), "\n")
            if startswith(line, r"\s*#")
                # comments
                continue
            end
            if !contains(line, r"[^\s]+")
                # empty line
                continue
            end
            c += 1
        end
    end
    return c
end
function count_lines_of_code_in_folder(folder)
    c = 0
    for filename in readdir(folder; join=true)
        c_file = count_lines_of_code_in_file(filename)
        println(filename, ": ",c_file)
        c += c_file
    end
    return c
end

c1 = count_lines_of_code_in_folder("src/py/analysis")
c2 = count_lines_of_code_in_folder("src/py/ast_utils")
c1 + c2
count_lines_of_code_in_folder("src/py/ppls")

c1 = count_lines_of_code_in_folder("src/jl/analysis")
c2 = count_lines_of_code_in_folder("src/jl/ast")
c1 + c2
count_lines_of_code_in_folder("src/jl/ppls")
