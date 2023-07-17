
@testset "symbolic" begin
    @test TypedSymbol("X") == TypedSymbol("X")
    @test TypedSymbol("X") != TypedSymbol("X", "Int")
    X = TypedSymbol("X")
    @test Not(Not(X)) == X
    Y = TypedSymbol("Y")
    @test Operation("f", X, Y) == Operation("f", X, Y)
    @test Not(Not(Operation("f", X, Y))) == Operation("f", X, Y)
    @test Constant("X") != TypedSymbol("X")
    @test Constant(true) == Constant(true)

    source_code = """
    @gen function model(I:: Bool)
        A  ~ bernoulli(0.5)

        if A == 1
            B ~ normal(0., 1.)
        else
            B ~ gamma(1, 1)

            if B > 1 && I
                {:C} ~ beta(1, 1)
            end
        end
        if B < 1 && I
            {:D} ~ normal(0., 1.)
        end
        if B < 2
            {:D} ~ normal(0., 2.) # Duplicated
            {:E} ~ normal(0., 1.)
        end
    end
    """

    syntax_tree = get_syntax_tree_for_str(source_code)
    replace_sample_syntax!(Gen(), syntax_tree)

    func = syntax_tree.root_node[1,2]
    A = func[2, 1]
    B1 = func[2, 2, 2, 1]
    B2 = func[2, 2, 3, 1]
    C = func[2, 2, 3, 2, 2, 1]
    D1 = func[2, 3, 2, 1]
    D2 = func[2, 4, 2, 1]
    E = func[2, 4, 2, 2]

    nodes = [A, B1, B2, C, D1, D2, E]
    node_to_symbol = Dict(
        A => TypedSymbol("A"),
        B1 => TypedSymbol("B"),
        B2 => TypedSymbol("B"),
        C => TypedSymbol("C"),
        D1 => TypedSymbol("D"),
        D2 => TypedSymbol("D"),
        E => TypedSymbol("E")
    )


    evaluator = SymbolicEvaluator(Dict(node=>[] for node in nodes), func, node_to_symbol)
    visit(evaluator, func)
    [length(evaluator.result[node]) for node in nodes] == [12, 4, 8, 4, 6, 6, 6]

    result = get_path_condition_for_nodes(func, nodes, node_to_symbol)

    @test result[A] == Constant(true)
    @test result[B1] == Operation("==", TypedSymbol("A"), Constant(1))
    @test result[B2] == Not(Operation("==", TypedSymbol("A"), Constant(1)))
    @test result[C] == Operation("&", result[B2], Operation("&", Operation(">", TypedSymbol("B"), Constant(1)), TypedSymbol("I", "Bool")))
    @test result[D1] == Operation("&", Operation("<", TypedSymbol("B"), Constant(1)), TypedSymbol("I", "Bool"))
    @test result[D2] == Operation("<", TypedSymbol("B"), Constant(2))
    @test result[E] == Operation("<", TypedSymbol("B"), Constant(2))


    source_code = """
    @gen function model(I)
        if I > 0
            m = I-1
        else
            m = 2*I
        end
        
        if 0 < m
            A ~ bernoulli(0.5)
        else
            B ~ normal(0., 1.)
        end
    end
    """

    syntax_tree = get_syntax_tree_for_str(source_code)
    replace_sample_syntax!(Gen(), syntax_tree)

    func = syntax_tree.root_node[1,2]
    A = func[2,2,2,1]
    B = func[2,2,3,1]

    nodes = [A, B]
    node_to_symbol = Dict(
        A => TypedSymbol("A"),
        B => TypedSymbol("B")
    )

    result = get_path_condition_for_nodes(func, nodes, node_to_symbol)
    @test path_condition_to_str(result[A]) == "|(&(!(>(Real(I),Constant(0))),<(Constant(0),*(Constant(2),Real(I)))),&(>(Real(I),Constant(0)),<(Constant(0),-(Real(I),Constant(1)))))"
    @test path_condition_to_str(result[B]) == "|(&(!(>(Real(I),Constant(0))),!(<(Constant(0),*(Constant(2),Real(I))))),&(>(Real(I),Constant(0)),!(<(Constant(0),-(Real(I),Constant(1))))))"
end
