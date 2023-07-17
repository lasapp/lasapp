
@testset "data control flow" begin

    source_code = """
    x = 1
    y = x
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    x_ass = scoped_tree.root_node[1]
    y_ass = scoped_tree.root_node[2]

    @test length(scoped_tree.all_definitions) == 2

    data_deps = collect(data_deps_for_node(scoped_tree, x_ass))
    @test length(data_deps) == 0

    data_deps = collect(data_deps_for_node(scoped_tree, y_ass))
    @test length(data_deps) == 1 && data_deps == scoped_tree.all_definitions[[1]]

    source_code = """
    x = 1
    x = x
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    
    x_ass = scoped_tree.root_node[1]
    x_ass_2 = scoped_tree.root_node[2]
    
    @test length(scoped_tree.all_definitions) == 2
    
    data_deps = collect(data_deps_for_node(scoped_tree, x_ass))
    @test length(data_deps) == 0
    
    data_deps = collect(data_deps_for_node(scoped_tree, x_ass_2))
    @test length(data_deps) == 1 && data_deps == scoped_tree.all_definitions[[1]]
    

    source_code = """
    x = 1
    i = 1
    y[i] = x
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    x_ass = scoped_tree.root_node[1]
    i_ass = scoped_tree.root_node[2]
    y_ass = scoped_tree.root_node[3]

    @test length(scoped_tree.all_definitions) == 3

    data_deps = collect(data_deps_for_node(scoped_tree, x_ass))
    @test length(data_deps) == 0

    data_deps = collect(data_deps_for_node(scoped_tree, y_ass))
    @test length(data_deps) == 2 && length(data_deps ∩ scoped_tree.all_definitions[[1,2]]) == 2


    source_code = """
    function outer()
        x = 1
        z = 1
        for i in 1:10 
            y = i^2
            z = y
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    i_ass = scoped_tree.root_node[1,2,3,1]
    i2 = scoped_tree.root_node[1,2,3,2,1,2]
    y_ass = scoped_tree.root_node[1,2,3,2,1]
    y2 = scoped_tree.root_node[1,2,3,2,2,2]
    z_ass = scoped_tree.root_node[1,2,3,2,2]

    @test length(scoped_tree.all_definitions) == 5

    data_deps = collect(data_deps_for_node(scoped_tree, i_ass))
    @test length(data_deps) == 0

    data_deps = collect(data_deps_for_node(scoped_tree, i2))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[3]

    data_deps = collect(data_deps_for_node(scoped_tree, y_ass))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[3]

    data_deps = collect(data_deps_for_node(scoped_tree, y2))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[4]

    data_deps = collect(data_deps_for_node(scoped_tree, z_ass))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[4]



    source_code = """
    function outer()
        z = 1
        if z < 0
            z = 2
        else
            z = 3
            x = z
        end
        y = z
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)


    @test length(scoped_tree.all_definitions) == 5

    x_ass = scoped_tree.root_node[1,2,2,3,2]
    y_ass = scoped_tree.root_node[1,2,3]

    data_deps = collect(data_deps_for_node(scoped_tree, x_ass))
    @test length(data_deps) ==2 && length(data_deps ∩ scoped_tree.all_definitions[[1,3]]) == 2

    data_deps = collect(data_deps_for_node(scoped_tree, y_ass))
    @test length(data_deps) == 3 && length(data_deps ∩ scoped_tree.all_definitions[[1,2,3]]) == 3



    source_code = """
    function A(y, z)
        return y + z
    end
    function B()
        y = 1
        z = 2
        x = A(y, z)
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    x_ass = scoped_tree.root_node[2,2,3]
    data_deps = collect(data_deps_for_node(scoped_tree, x_ass))
    @test length(scoped_tree.all_definitions) == 3 && length(scoped_tree.all_functions) == 2
    @test length(data_deps) == 3 && length(data_deps ∩ (scoped_tree.all_definitions[[1,2]] ∪ scoped_tree.all_functions[[1]])) == 3


    source_code = """
    function A()
        y = 1
        z = 2
        return y + z
    end
    function B(x)
        y = 1
        if x < 1
            return y
        else
            z = 2
            return z
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    
    A = scoped_tree.root_node[1]
    data_deps = collect(data_deps_for_node(scoped_tree, A))
    @test length(data_deps) == 2 && length(data_deps ∩ (scoped_tree.all_definitions[[1,2]])) == 2
    
    B = scoped_tree.root_node[2]
    data_deps = collect(data_deps_for_node(scoped_tree, B))
    @test length(data_deps) == 2 && length(data_deps ∩ (scoped_tree.all_definitions[[3,4]])) == 2
    

    source_code = """
    for i in 1:10
        if i < 5
            j = 1
            while j < 3
                j *= 2
            end
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    for_node = scoped_tree.root_node[1]
    if_node = for_node[2,1]
    while_node = if_node[2,2]
    j = while_node[2,1]
    control_parents = control_parents_for_node(scoped_tree, j)
    @test length(control_parents ∩ [while_node, if_node, for_node]) == 3


    source_code = """
    function A(x, y)
        if x < 5
            return 1
        end
        if y < 5
            return 2
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    
    A = scoped_tree.root_node[1]
    
    control_parents = control_parents_for_node(scoped_tree, A)
    if_1 = A[2,1]
    if_2 = A[2,2]
    
    @test length(control_parents ∩ [if_1, if_2]) == 2


    source_code = "[x for x in 1:10]"
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    generator = scoped_tree.root_node[1,1]
    x_ass = generator[2]
    x_use = generator[1]


    control_parents = control_parents_for_node(scoped_tree, x_use)
    @test length(control_parents) == 1 && control_parents[1] == generator

    control_parents = control_parents_for_node(scoped_tree, x_ass)
    @test length(control_parents) == 0


    data_deps = collect(data_deps_for_node(scoped_tree, x_use))
    @test length(data_deps) == 0 # for now, in future can depend on x_ass (now only control dependend)

    source_code = """
    function main()
        x = 0
        while x < 0.5
            x = rand()
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    func_body = scoped_tree.root_node[1,2]
    while_node = func_body[2]
    data_deps = collect(data_deps_for_node(scoped_tree, while_node[1]))
    x_zero = func_body[1]
    x_rand = while_node[2,1]
    data_deps_nodes = [dep.node for dep in data_deps]
    @test x_zero in data_deps_nodes
    @test x_rand in data_deps_nodes

    source_code = """
    function A(x, y)
        if x < 5
            return 1
        end
        function B()
            if y < 5
                return 2
            end
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    
    A = scoped_tree.root_node[1]
    
    control_parents = control_parents_for_node(scoped_tree, A)
    if_1 = A[2,1]
    
    @test control_parents == [if_1]

    source_code = """
    function A(x, y)
        if x < 5
            return 1
        end
        function B()
            if y < 5
                return 2
            end
        end
        z = 3
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    A = scoped_tree.root_node[1]
    z = A[2,3]
    control_parents = control_parents_for_node(scoped_tree, z)
    if_1 = A[2,1]

    @test control_parents == [if_1]
end
