
@testset "interval arithmetic" begin
    @test Interval(-1,2) + Interval(2,3) == Interval(1,5)
    @test Interval(-1,2) * Interval(2,3) == Interval(-3,6)
    @test Interval(-1,2) - Interval(2,3) == Interval(-4,0)
    @test Interval(-1,2) / Interval(2,3) == Interval(-0.5, 1.0)
    @test Interval(-1,2) * Interval(3) == Interval(-3,6)
    @test Interval(-1,2) ∪ Interval(2,3) == Interval(-1,3)
    @test Interval(-1,2) ∪ Interval(3,4) == Interval(-1,4)
    @test Interval(-1,2) ^ Interval(2,3) == Interval(0, Inf)
    @test Interval(-1,2) ^ Interval(2) == Interval(0,4)
    @test Interval(-1,2) ^ Interval(3) == Interval(-1,8)


    source_code = """
    a = x + y
    b = a * z
    exp(b)
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)

    node_to_evaluate = syntax_tree.root_node[3]
    x = Interval(-1,2)
    y = Interval(2,3)
    z = Interval(2)
    result = static_interval_eval(cfg_progr_repr, node_to_evaluate, Dict(:x => x, :y => y, :z => z))
    @test result == exp((x + y) * z)

    source_code = """
    if x < 3
        a = x + y
    else
        a = x - y
    end
    b = a * z
    exp(b)
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    node_to_evaluate = syntax_tree.root_node[3]
    result = static_interval_eval(cfg_progr_repr, node_to_evaluate, Dict(:x => x, :y => y, :z => z))
    @test result == exp(((x + y) ∪ (x - y)) * z)


    source_code = """
    if x < 3
        a = x + y()
    else
        a = x - y()
    end
    b = a * z
    exp(b)
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    node_to_evaluate = syntax_tree.root_node[3]
    result = static_interval_eval(cfg_progr_repr, node_to_evaluate, Dict(:x => x, :y => y, :z => z))
    @test result == exp(((x + y) ∪ (x - y)) * z)

    source_code = """
    x = 1
    while true
        x = x + 1
    end
    exp(x)
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    cfg_progr_repr = get_cfg_representation(scoped_tree)
    
    node_to_evaluate = syntax_tree.root_node[3]
    @test_throws StackOverflowError _static_interval_eval(cfg_progr_repr, node_to_evaluate, Dict{Symbol, Interval}())
    @test Interval(-Inf, Inf) == static_interval_eval(cfg_progr_repr, node_to_evaluate, Dict{Symbol, Interval}())
    
end

