# include("../../analysis/cfg.jl")
# include("../../analysis/data_control_flow.jl")

function get_nodes(defs::AbstractVector{<:NameDefinition})
    return Set{SyntaxNode}([def.node for def in defs])
end

function get_node_by_sourcetext(cfg::CFG, text::String, type::Union{Nothing,CFGNodeType}=nothing)
    for node in cfg.nodes
        if JuliaSyntax.sourcetext(node.syntaxnode) == text && (isnothing(type) || node.type == type)
            return node
        end
    end
    return nothing
end
function get_node_by_sexpr(cfg::CFG, text::String, type::Union{Nothing,CFGNodeType}=nothing)
    for node in cfg.nodes
        if string(node.syntaxnode) == text && (isnothing(type) || node.type == type)
            return node
        end
    end
    return nothing
end

@testset "data control flow" begin

    source_code = """
    x = 1
    y = x
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)

    x_ass = scoped_tree.root_node[1]
    y_ass = scoped_tree.root_node[2]

    @test length(scoped_tree.all_definitions) == 2

    data_deps = data_deps_for_syntaxnode(cfg_progr_repr, x_ass)
    @test length(data_deps) == 0

    data_deps = data_deps_for_syntaxnode(cfg_progr_repr, y_ass)
    @test length(data_deps) == 1 && data_deps == get_nodes(scoped_tree.all_definitions[[1]])

    source_code = """
    x = 1
    x = x
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)

    x_ass = scoped_tree.root_node[1]
    x_ass_2 = scoped_tree.root_node[2]

    @test length(scoped_tree.all_definitions) == 2

    data_deps = data_deps_for_syntaxnode(cfg_progr_repr, x_ass)
    @test length(data_deps) == 0

    data_deps = data_deps_for_syntaxnode(cfg_progr_repr, x_ass_2)
    @test length(data_deps) == 1 && data_deps == get_nodes(scoped_tree.all_definitions[[1]])
    

    source_code = """
    x = 1
    i = 1
    y[i] = x
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    x_ass = scoped_tree.root_node[1]
    i_ass = scoped_tree.root_node[2]
    y_ass = scoped_tree.root_node[3]
    
    @test length(scoped_tree.all_definitions) == 3
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, x_ass))
    @test length(data_deps) == 0
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, y_ass))
    @test length(data_deps) == 2 && length(data_deps ∩ get_nodes(scoped_tree.all_definitions[[1,2]])) == 2


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
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    i_ass = scoped_tree.root_node[1,2,3,1]
    i2 = scoped_tree.root_node[1,2,3,2,1,2]
    y_ass = scoped_tree.root_node[1,2,3,2,1]
    y2 = scoped_tree.root_node[1,2,3,2,2,2]
    z_ass = scoped_tree.root_node[1,2,3,2,2]
    
    @test length(scoped_tree.all_definitions) == 5
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, i_ass))
    @test length(data_deps) == 0
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, i2))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[3].node
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, y_ass))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[3].node
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, y2))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[4].node
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, z_ass))
    @test length(data_deps) == 1 && data_deps[1] == scoped_tree.all_definitions[4].node



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
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    
    @test length(scoped_tree.all_definitions) == 5
    
    x_ass = scoped_tree.root_node[1,2,2,3,2]
    y_ass = scoped_tree.root_node[1,2,3]
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, x_ass))
    @test length(data_deps) == 1 && length(data_deps ∩ get_nodes(scoped_tree.all_definitions[[3]])) == 1
    
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, y_ass))
    @test length(data_deps) == 2 && length(data_deps ∩ get_nodes(scoped_tree.all_definitions[[2,3]])) == 2


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
    cfg_progr_repr = get_cfg_representation(scoped_tree)

    x_ass = scoped_tree.root_node[2,2,3]
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, x_ass))
    @test length(scoped_tree.all_definitions) == 3 && length(scoped_tree.all_functions) == 2
    @test length(data_deps) == 3 && length(data_deps ∩ get_nodes(scoped_tree.all_definitions[[1,2]] ∪ scoped_tree.all_functions[[1]])) == 3

    # test pass until here

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
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    A = scoped_tree.root_node[1]
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, A))
    @test length(data_deps) == 2 && length(data_deps ∩ get_nodes(scoped_tree.all_definitions[[1,2]])) == 2
    
    B = scoped_tree.root_node[2]
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, B))
    @test length(data_deps) == 2 && length(data_deps ∩ get_nodes(scoped_tree.all_definitions[[3,4]])) == 2
    

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
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    for_node = scoped_tree.root_node[1]
    if_node = for_node[2,1]
    while_node = if_node[2,2]
    j = while_node[2,1]
    control_parents = control_parents_for_syntaxnode(cfg_progr_repr, j)
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
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    A = scoped_tree.root_node[1]
    
    control_parents = control_parents_for_syntaxnode(cfg_progr_repr, A)
    if_1 = A[2,1]
    if_2 = A[2,2]
    
    @test length(control_parents ∩ [if_1, if_2]) == 2

    # TODO? implement support for generators
    # source_code = "[x for x in 1:10]"
    # syntax_tree = get_syntax_tree_for_str(source_code)
    # scoped_tree = get_scoped_tree(syntax_tree)
    # cfg_progr_repr = get_cfg_representation(scoped_tree)

    # generator = scoped_tree.root_node[1,1]
    # x_ass = generator[2]
    # x_use = generator[1]


    # control_parents = control_parents_for_syntaxnode(cfg_progr_repr, x_use)
    # @test length(control_parents) == 1 && control_parents[1] == generator

    # control_parents = control_parents_for_syntaxnode(cfg_progr_repr, x_ass)
    # @test length(control_parents) == 0


    # data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, x_use))
    # @test length(data_deps) == 0 # for now, in future can depend on x_ass (now only control dependend)

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
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    func_body = scoped_tree.root_node[1,2]
    while_node = func_body[2]
    data_deps = collect(data_deps_for_syntaxnode(cfg_progr_repr, while_node[1]))
    x_zero = func_body[1]
    x_rand = while_node[2,1]
    @test x_zero in data_deps
    @test x_rand in data_deps

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
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    A = scoped_tree.root_node[1]
    
    control_parents = control_parents_for_syntaxnode(cfg_progr_repr, A)
    if_1 = A[2,1]
    
    @test control_parents == Set([if_1])

    source_code = """
    function A(x, y)
        if x < 5
            return 1
        end
        z = 3
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)

    A = scoped_tree.root_node[1]
    
    z = A[2,2]
    control_parents = control_parents_for_syntaxnode(cfg_progr_repr, z)
    if_1 = A[2,1]
    
    @test control_parents == Set([if_1])


    source_code = """
    function A(x, y)
        if x < 5
            1
        end
        z = 3
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)

    A = scoped_tree.root_node[1]

    z = A[2,2]
    control_parents = control_parents_for_syntaxnode(cfg_progr_repr, z)
    @test control_parents == Set([])


    s = """
    x, y, _ = func()
    x = 2
    _ = (x, y)
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    assign_node = get_node_by_sourcetext(cfg, "x, y, _ = func()")
    # [node.val for node in get_assignnode_targets(assign_node)] == [:x, :y, :_]

    x = syntax_tree.root_node[6,2,1]
    y = syntax_tree.root_node[6,2,2]

    @test get_RDs(scoped_tree, cfg.endnode, x) == Set([get_node_by_sexpr(cfg, "(= x 2)")])

    @test get_RDs(scoped_tree, cfg.endnode, y) == Set([get_node_by_sexpr(cfg, "(= y (ref __TMP__node_1 2))")])


    s = """
    x = 1
    if test1
        x = 2
    else
        if test2
            x = 3
        end
        x = 4
        if test3
            x = 5
            x = 6
        end
    end
    _ = x
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)

    x = syntax_tree.root_node[3,2]
    @test get_RDs(scoped_tree, cfg.endnode, x) == Set([
        get_node_by_sourcetext(cfg, "x = 6"),
        get_node_by_sourcetext(cfg, "x = 4"),
        get_node_by_sourcetext(cfg, "x = 2"),
    ])

    cfgnode = get_node_by_sourcetext(cfg, "x = 6")
    @test get_BPs(scoped_tree, cfgnode) == Set([
        get_node_by_sourcetext(cfg, "test3", BRANCH_NODE),
        get_node_by_sourcetext(cfg, "test1", BRANCH_NODE)
    ])

    cfgnode = get_node_by_sourcetext(cfg, "x = 2")
    @test get_BPs(scoped_tree, cfgnode) == Set([
        get_node_by_sourcetext(cfg, "test1", BRANCH_NODE)
    ])

    cfgnode = get_node_by_sourcetext(cfg, "x = 3")
    @test get_BPs(scoped_tree, cfgnode) == Set([
        get_node_by_sourcetext(cfg, "test2", BRANCH_NODE),
        get_node_by_sourcetext(cfg, "test1", BRANCH_NODE)
    ])

    cfgnode = get_node_by_sourcetext(cfg, "x = 4")
    @test get_BPs(scoped_tree, cfgnode) == Set([
        get_node_by_sourcetext(cfg, "test1", BRANCH_NODE)
    ])

    cfgnode = get_node_by_sourcetext(cfg, "_ = x")
    @test isempty(get_BPs(scoped_tree, cfgnode))

    s = """
    x = 1
    while x < 10
        x += 1
    end
    _ = x
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)

    while_body = get_node_by_sourcetext(cfg, "x += 1")
    x = syntax_tree.root_node[3,2]
    @test get_RDs(scoped_tree, while_body, x) == Set([
        get_node_by_sourcetext(cfg, "x += 1"),
        get_node_by_sourcetext(cfg, "x = 1")
    ])

    @test get_BPs(scoped_tree, while_body) == Set([
        get_node_by_sourcetext(cfg, " x < 10", BRANCH_NODE),
    ])
    end_node = get_node_by_sourcetext(cfg, "_ = x")
    @test get_BPs(scoped_tree, end_node) == Set()

    s = """
    if test1
        x = 1
        x = 2
    else
        x = 3
    end
    x = 4
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)
    b = get_node_by_sourcetext(cfg, "test1", BRANCH_NODE)
    j = get_node_by_sourcetext(cfg, "test1", JOIN_NODE)
    e = cfg.endnode

    @test is_reachable(b, j)

    n = get_node_by_sourcetext(cfg, "x = 1")
    @test is_on_path_between_nodes(n, b, j)

    n = get_node_by_sourcetext(cfg, "x = 2")
    @test is_on_path_between_nodes(n, b, j)

    n = get_node_by_sourcetext(cfg, "x = 3")
    @test is_on_path_between_nodes(n, b, j)

    n = get_node_by_sourcetext(cfg, "x = 4")
    @test !is_on_path_between_nodes(n, b, j)
    @test is_on_path_between_nodes(n, b, e)


    s = """
    x = 0
    while test1
        x = 1
    end
    while test2
        x = 2
    end
    y = x
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    cfg = cfg_progr_repr.cfgs[syntax_tree.root_node]
    @test verify_cfg(cfg)
    b1 = get_node_by_sourcetext(cfg, "test1", BRANCH_NODE)
    j1 = get_node_by_sourcetext(cfg, "test1", JOIN_NODE)

    b2 = get_node_by_sourcetext(cfg, "test2", BRANCH_NODE)
    j2 = get_node_by_sourcetext(cfg, "test2", JOIN_NODE)

    @test is_reachable(b1, j1)
    @test is_reachable(b2, j2)
    @test is_reachable(b1, j2)

    n = get_node_by_sourcetext(cfg, "x = 1")
    @test is_on_path_between_nodes(n, b1, j1)
    @test !is_on_path_between_nodes(n, b2, j2)
    @test is_on_path_between_nodes(n, b1, j2)

    n = get_node_by_sourcetext(cfg, "x = 2")
    @test !is_on_path_between_nodes(n, b1, j1)
    @test is_on_path_between_nodes(n, b2, j2)
    @test is_on_path_between_nodes(n, b1, j2)

    n = get_node_by_sourcetext(cfg, "y = x")
    @test !is_on_path_between_nodes(n, b1, j1)
    @test !is_on_path_between_nodes(n, b2, j2)
    @test !is_on_path_between_nodes(n, b1, j2)


    n = get_node_by_sourcetext(cfg, "y = x")
    x = n.syntaxnode[2]
    data_deps_for_syntaxnode(cfg_progr_repr, x) == Set([
        get_node_by_sourcetext(cfg, "x = 0").syntaxnode,
        get_node_by_sourcetext(cfg, "x = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "x = 2").syntaxnode
    ])



    s = """
    function test(a, a2::Int, b=1, b2::Int=1; c, d=2, c2::Int, d2::Int=2)
        return a, a2, b, b2, c, d, c2, d2
    end
    """
    s = """
    function test(a, a2::Int, b=1, b2::Int=1; c, d=2, c2::Int, d2::Int=2)::Tuple
        return a, a2, b, b2, c, d, c2, d2
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    test_func = syntax_tree.root_node[1]

    return_expr = syntax_tree.root_node[1,2,1,1]
    @test data_deps_for_syntaxnode(cfg_progr_repr, return_expr) == Set(p for p in get_parameter_nodes_of_function(test_func))



    s = """
    function test(x; y = 1)
        return x + y
    end

    a = 1
    test(a)

    b = 1
    c = 1
    test(b, y=c)
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    cfg = cfg_progr_repr.cfgs[syntax_tree.root_node]

    x_arg = syntax_tree.root_node[1,1,2]
    y_arg = syntax_tree.root_node[1,1,3,1]

    @test data_deps_for_syntaxnode(cfg_progr_repr, x_arg) == Set([
        get_node_by_sourcetext(cfg, "a = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "b = 1").syntaxnode
    ])
    @test data_deps_for_syntaxnode(cfg_progr_repr, y_arg) == Set([
        get_node_by_sourcetext(cfg, "c = 1").syntaxnode
    ])



    s = """
    function test(a, a2::Int, b=1, b2::Int=1; c, d=2, c2::Int, d2::Int=2)
        return a, a2, b, b2, c, d, c2, d2
    end

    arg_a = 1
    arg_a2 = 1
    arg_c = 1
    arg_c2 = 1

    test(arg_a, arg_a2, c=arg_c, c2=arg_c2)

    b = 1
    d = 1
    test(arg_a, arg_a2, b, c=arg_c, c2=arg_c2, d2=d)
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    cfg = cfg_progr_repr.cfgs[syntax_tree.root_node]

    test_func = syntax_tree.root_node[1]
    a, a2, b, b2, c, d, c2, d2 = get_parameter_nodes_of_function(test_func)

    @test data_deps_for_syntaxnode(cfg_progr_repr, a) == Set([
        get_node_by_sourcetext(cfg, "arg_a = 1").syntaxnode
    ])
    @test data_deps_for_syntaxnode(cfg_progr_repr, b) == Set([
        get_node_by_sourcetext(cfg, "b = 1").syntaxnode
    ])
    @test isempty(data_deps_for_syntaxnode(cfg_progr_repr, b2))

    @test isempty(data_deps_for_syntaxnode(cfg_progr_repr, d))

    @test data_deps_for_syntaxnode(cfg_progr_repr, d2) == Set([
        get_node_by_sourcetext(cfg, "d = 1").syntaxnode
    ])

    @test data_deps_for_syntaxnode(cfg_progr_repr, c2) == Set([
        get_node_by_sourcetext(cfg, "arg_c2 = 1").syntaxnode
    ])

    func_sign = test_func[1]
    @test is_function_signature(func_sign)
    @test  data_deps_for_syntaxnode(cfg_progr_repr, func_sign) == Set([
        get_node_by_sourcetext(cfg, "arg_a = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "arg_a2 = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "arg_c = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "arg_c2 = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "b = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "d = 1").syntaxnode
    ])




    s = """
    function foo(x; y = 1)
        return x + y
    end

    if test1
        a = 1
    else
        a = 2
    end
    foo(a)

    if test2
        b = 1
        c = 1
        foo(b, y=c)
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    cfg = cfg_progr_repr.cfgs[syntax_tree.root_node]

    x_arg = syntax_tree.root_node[1,1,2]
    y_arg = syntax_tree.root_node[1,1,3,1]

    @test data_deps_for_syntaxnode(cfg_progr_repr, x_arg) == Set([
        get_node_by_sourcetext(cfg, "a = 1").syntaxnode,
        get_node_by_sourcetext(cfg, "a = 2").syntaxnode,
        get_node_by_sourcetext(cfg, "b = 1").syntaxnode
    ])
    @test data_deps_for_syntaxnode(cfg_progr_repr, y_arg) == Set([
        get_node_by_sourcetext(cfg, "c = 1").syntaxnode
    ])

    if_2 = syntax_tree.root_node[4]
    @test control_parents_for_syntaxnode(cfg_progr_repr, x_arg) == Set([if_2])
    @test control_parents_for_syntaxnode(cfg_progr_repr, x_arg) == Set([if_2])

end



