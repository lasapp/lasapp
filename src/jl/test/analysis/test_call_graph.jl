
@testset "call graph" begin
    source_code = """
    function A()
        A()
    end
    function B()
        A()
        C()
        !(true)
    end
    function C()
        A() + B()
    end
    function D()
        A()
    end
    """

    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    A = syntax_tree.root_node[1]
    B = syntax_tree.root_node[2]
    C = syntax_tree.root_node[3]
    D = syntax_tree.root_node[4]
    AB = C[2,1] # A() + B()
    call_graph = compute_call_graph(scoped_tree, C)
    @test !haskey(call_graph, D)
    @test call_graph[A] == [A]
    @test call_graph[B] == [A,C]
    @test call_graph[C] == [A,B]

    call_graph = compute_call_graph(scoped_tree, D)
    @test !haskey(call_graph, B) && !haskey(call_graph, C)
    @test call_graph[A] == [A]
    @test call_graph[D] == [A]

    call_graph = compute_call_graph(scoped_tree, AB)
    @test !haskey(call_graph, D)
    @test call_graph[A] == [A]
    @test call_graph[B] == [A,C]
    @test call_graph[C] == [A,B]

    source_code = """
    function A()
        A()
        return 'A'
    end

    function B()
        return A()
    end

    function C()
        function D()
            C()
            return B()
        end
        function E()
            return D()
        end
        return E()
    end
    """

    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)


    A = syntax_tree.root_node[1]
    B = syntax_tree.root_node[2]
    C = syntax_tree.root_node[3]
    D = syntax_tree.root_node[3,2,1]
    E = syntax_tree.root_node[3,2,2]

    call_graph = compute_call_graph(scoped_tree, nothing)


    @test call_graph[A] == [A]
    @test call_graph[B] == [A]
    @test call_graph[C] == [E]
    @test call_graph[D] == [C, B]
    @test call_graph[E] == [D]


    source_code = """
    @model function A()
        A()
    end

    @model function B()
        return A()
    end

    @model function C()
        return B()
    end

    """

    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    A_macro = syntax_tree.root_node[1]
    A = A_macro[2]
    B_macro = syntax_tree.root_node[2]
    B = B_macro[2]
    C_macro = syntax_tree.root_node[3]
    C = C_macro[2]

    call_graph = compute_call_graph(scoped_tree, nothing)
    @test call_graph[A] == [A]
    @test call_graph[B] == [A]
    @test call_graph[C] == [B]

    call_graph = compute_call_graph(scoped_tree, C_macro)
    @test call_graph[A] == [A]
    @test call_graph[B] == [A]
    @test call_graph[C] == [B]
    @test call_graph[C_macro] == [B]

    call_graph = compute_call_graph(scoped_tree, B_macro)
    @test call_graph[A] == [A]
    @test call_graph[B] == [A]
    @test call_graph[B_macro] == [A]

    call_graph = compute_call_graph(scoped_tree, A_macro)
    @test call_graph[A] == [A]
    @test call_graph[A_macro] == [A]
    @test !haskey(call_graph, B)
end
