
@testset "cfg" begin

    s = """
    x = 1
    y = [[2,2]]
    z = f(3,x=x,y=y[1])
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "ASSIGN(x = 1)" => "ASSIGN(y = [[2,2]])",
        "ASSIGN(y = [[2,2]])" => "ASSIGN(z = f(3,x=x,y=y[1]))",
        "START" => "ASSIGN(x = 1)",
        "ASSIGN(z = f(3,x=x,y=y[1]))" => "END",
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    if test1
        x = 1
    end
    if test2
        y = 2
    elseif test3
        z = 3
    else
        a = 4
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "ASSIGN(z = 3)" => "JOIN(test3)",
        "BRANCH(test2)" => "ASSIGN(y = 2)",
        "JOIN(test3)" => "JOIN(test2)",
        "BRANCH(test2)" => "BRANCH(test3)",
        "BRANCH(test3)" => "ASSIGN(z = 3)",
        "BRANCH(test3)" => "ASSIGN(a = 4)",
        "ASSIGN(a = 4)" => "JOIN(test3)",
        "ASSIGN(y = 2)" => "JOIN(test2)",
        "BRANCH(test1)" => "JOIN(test1)",
        "ASSIGN(x = 1)" => "JOIN(test1)",
        "START" => "BRANCH(test1)",
        "JOIN(test1)" => "BRANCH(test2)",
        "JOIN(test2)" => "END",
        "BRANCH(test1)" => "ASSIGN(x = 1)",
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    while i > 0
        i -= 1
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "JOIN( i > 0)" => "END"
        "BRANCH( i > 0)" => "JOIN( i > 0)"
        "ASSIGN(i -= 1)" => "BRANCH( i > 0)"
        "START" => "BRANCH( i > 0)"
        "BRANCH( i > 0)" => "ASSIGN(i -= 1)"
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    for i in 1:10
        x += 1
        x += 2
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "BRANCH( i in 1:10)" => "ASSIGN( i in 1:10)"
        "ASSIGN(x += 1)" => "ASSIGN(x += 2)"
        "ASSIGN( i in 1:10)" => "ASSIGN(x += 1)"
        "START" => "BRANCH( i in 1:10)"
        "BRANCH( i in 1:10)" => "JOIN( i in 1:10)"
        "ASSIGN(x += 2)" => "BRANCH( i in 1:10)"
        "JOIN( i in 1:10)" => "END"
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    function foo()
        x = 1
        x
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:foo]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "ASSIGN(x = 1)" => "EXPR(x)",
        "RETURN(x)" => "JOIN(foo())",
        "JOIN(foo())" => "END",
        "FUNCSTART" => "ASSIGN(x = 1)",
        "EXPR(x)" => "RETURN(x)",
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    function foo()
        x = 1
        return x
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:foo]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "RETURN(return x)" => "JOIN(foo())"
        "JOIN(foo())" => "END"
        "ASSIGN(x = 1)" => "RETURN(return x)"
        "FUNCSTART" => "ASSIGN(x = 1)"
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    function foo()
        if test1
            return a
        end
        if test2
            x
        elseif test3
            y
        else
            z
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:foo]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "BRANCH(test1)" => "RETURN(return a)",
        "EXPR(z)" => "RETURN(z)",
        "RETURN(return a)" => "JOIN(foo())",
        "EXPR(y)" => "RETURN(y)",
        "BRANCH(test2)" => "BRANCH(test3)",
        "BRANCH(test3)" => "EXPR(z)",
        "BRANCH(test2)" => "EXPR(x)",
        "RETURN(x)" => "JOIN(foo())",
        "BRANCH(test1)" => "JOIN(test1)",
        "JOIN(foo())" => "END",
        "RETURN(y)" => "JOIN(foo())",
        "RETURN(z)" => "JOIN(foo())",
        "BRANCH(test3)" => "EXPR(y)",
        "JOIN(test1)" => "BRANCH(test2)",
        "FUNCSTART" => "BRANCH(test1)",
        "EXPR(x)" => "RETURN(x)"
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    function foo()
        if test1
            return a
        end
        if test2
            x
        elseif test3
            y
        else
            z
        end
        b
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:foo]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "BRANCH(test1)" => "RETURN(return a)",
        "RETURN(return a)" => "JOIN(foo())",
        "EXPR(z)" => "JOIN(test3)",
        "JOIN(test3)" => "JOIN(test2)",
        "RETURN(b)" => "JOIN(foo())",
        "EXPR(y)" => "JOIN(test3)",
        "BRANCH(test2)" => "BRANCH(test3)",
        "BRANCH(test3)" => "EXPR(z)",
        "BRANCH(test2)" => "EXPR(x)",
        "BRANCH(test1)" => "JOIN(test1)",
        "JOIN(foo())" => "END",
        "EXPR(b)" => "RETURN(b)",
        "BRANCH(test3)" => "EXPR(y)",
        "JOIN(test1)" => "BRANCH(test2)",
        "EXPR(x)" => "JOIN(test2)",
        "FUNCSTART" => "BRANCH(test1)",
        "JOIN(test2)" => "EXPR(b)"
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    
    s = """
    function foo()
        x = 1
        y = 2
        if x > y
            return x
        end
        return y
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:foo]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "RETURN(return y)" => "JOIN(foo())",
        "RETURN(return x)" => "JOIN(foo())",
        "ASSIGN(y = 2)" => "BRANCH( x > y)",
        "JOIN(foo())" => "END",
        "ASSIGN(x = 1)" => "ASSIGN(y = 2)",
        "BRANCH( x > y)" => "RETURN(return x)",
        "FUNCSTART" => "ASSIGN(x = 1)",
        "JOIN( x > y)" => "RETURN(return y)",
        "BRANCH( x > y)" => "JOIN( x > y)",
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    s = """
    i = 1
    while true
        i += 1
        if i % 2 == 1
            i = 2*i + 1
            continue
        elseif i > 1000
            i = i / 2
        elseif i > 10000
            break
        else
            i = 3 * i
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:toplevel]
    @test verify_cfg(cfg)
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "JOIN( i > 1000)" => "JOIN( i % 2 == 1)",
        "BRANCH(true)" => "ASSIGN(i += 1)",
        "ASSIGN(i = 3 * i)" => "JOIN( i > 10000)",
        "BRANCH( i > 10000)" => "BREAK",
        "START" => "ASSIGN(i = 1)",
        "BRANCH( i % 2 == 1)" => "ASSIGN(i = 2*i + 1)",
        "CONTINUE" => "BRANCH(true)",
        "ASSIGN(i = i / 2)" => "JOIN( i > 1000)",
        "JOIN(true)" => "END",
        "BRANCH( i > 1000)" => "BRANCH( i > 10000)",
        "BREAK" => "JOIN(true)",
        "BRANCH( i > 1000)" => "ASSIGN(i = i / 2)",
        "ASSIGN(i += 1)" => "BRANCH( i % 2 == 1)",
        "JOIN( i % 2 == 1)" => "BRANCH(true)",
        "BRANCH( i > 10000)" => "ASSIGN(i = 3 * i)",
        "BRANCH(true)" => "JOIN(true)",
        "BRANCH( i % 2 == 1)" => "BRANCH( i > 1000)",
        "ASSIGN(i = 2*i + 1)" => "CONTINUE",
        "JOIN( i > 10000)" => "JOIN( i > 1000)",
        "ASSIGN(i = 1)" => "BRANCH(true)",
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
    
    s = """
    x = [1,2]
    y = 1
    y = x[1]
    (x,y)
    """
    syntax_tree = get_syntax_tree_for_str(s)
    scoped_tree = get_scoped_tree(syntax_tree)
    @test all(is_container == (identifier.val == :x) for (identifier, is_container) in scoped_tree.is_container_variable)
    
    
    s = """
    function test(a, a2::Int, b=1, b2::Int=1; c, d=2, c2::Int, d2::Int=2)
    end
    """
    syntax_tree = get_syntax_tree_for_str(s)
    test_func = syntax_tree.root_node[1]
    scoped_tree = get_scoped_tree(syntax_tree)
    cfgs = get_cfgs(scoped_tree);
    cfg = cfgs[:test]
    @test verify_cfg(cfg)
    
    # ScopeTree test
    test_func_scope = scoped_tree.topscope.children[1]
    @test test_func_scope.node == test_func
    # arguments of function definition belong to function scope
    @test all(scoped_tree.identifier_to_scope[get_parameter_identifier(p)] == test_func_scope for p in get_parameter_nodes_of_function(test_func))
    
    edges = Set([short_node_string(x) => short_node_string(y) for (x,y) in get_cfg_edges(cfg)])
    gt_edges = Set([
        "FUNCARG(c)" => "FUNCARG(d=2)",
        "FUNCARG(a)" => "FUNCARG(a2::Int)",
        "RETURN()" => "JOIN(test(a, a2::Int, b=1, b2::Int=1; c, d=2, c2::Int, d2::Int=2))",
        "FUNCARG(b=1)" => "FUNCARG(b2::Int=1)",
        "FUNCSTART" => "FUNCARG(a)",
        "FUNCARG(b2::Int=1)" => "FUNCARG(c)",
        "FUNCARG(d=2)" => "FUNCARG(c2::Int)",
        "FUNCARG(a2::Int)" => "FUNCARG(b=1)",
        "JOIN(test(a, a2::Int, b=1, b2::Int=1; c, d=2, c2::Int, d2::Int=2))" => "END",
        "FUNCARG(d2::Int=2)" => "RETURN()",
        "FUNCARG(c2::Int)" => "FUNCARG(d2::Int=2)",
    ])
    for e in edges
        @test e in gt_edges
    end
    for gt_e in gt_edges
        @test gt_e in edges
    end
    
end