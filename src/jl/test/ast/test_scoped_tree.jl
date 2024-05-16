
@testset "ScopedTree" begin

    source_code = "x = 1"
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    @test length(scoped_tree.topscope.children) == 0
    @test scoped_tree.topscope.kind == :global
    @test :x in scoped_tree.topscope.symbols


    source_code = """
    x = 1
    a,b,c = 2,3,4
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    @test length(scoped_tree.all_definitions) == 5
    @test [def.name for def in scoped_tree.all_definitions] == [:x, :__TMP__node_4, :a, :b, :c]
    @test scoped_tree.topscope.symbols == Set([:__TMP__node_4, :x, :a, :b, :c])

    source_code = """
    f = 1
    function f(y) end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    @test_throws AssertionError get_scoped_tree(syntax_tree) # name conflict


    source_code = """
    f = 1
    for i in 1:10
        f += 1
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    @test_logs (:warn, "f is defined globally and assigned in soft scope. This is ambiguous. Assuming interactive context.") get_scoped_tree(syntax_tree)

    source_code = """
    function outer()
        x = 1
        function f(y) 
            x = y
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    @test_throws ErrorException get_scoped_tree(syntax_tree) # impure function


    source_code = """
    function outer()
        x = 1
        function inner(z) 
            y = 2
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    global_scope = scoped_tree.topscope
    outer_scope = global_scope.children[1]
    inner_scope = outer_scope.children[1]
    @test :outer in global_scope.symbols
    @test Set([:x, :inner]) == outer_scope.symbols
    @test Set([:y, :z]) == inner_scope.symbols
    x = scoped_tree.root_node[1,2,1,1]
    @test scoped_tree.identifier_to_scope[x] == outer_scope
    
    y = scoped_tree.root_node[1,2,2,2,1,1]
    @test scoped_tree.identifier_to_scope[y] == inner_scope

    outer = scoped_tree.root_node[1,1,1]
    @test scoped_tree.identifier_to_scope[outer] == global_scope
    
    inner = scoped_tree.root_node[1,2,2,1,1]
    @test scoped_tree.identifier_to_scope[inner] == outer_scope


    @test find_innermost_scope_for_node(global_scope, outer) == global_scope
    @test find_innermost_scope_for_node(global_scope, inner) == outer_scope

    source_code = """
    function outer()
        x = 1
        z = 1
        function inner(z) 
            y = 2
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    global_scope = scoped_tree.topscope
    outer_scope = global_scope.children[1]
    inner_scope = outer_scope.children[1]
    @test Set([:x, :inner, :z]) == outer_scope.symbols
    @test Set([:y, :z]) == inner_scope.symbols


    source_code = """
    function outer()
        x = 1
        z = 1
        for i in 1:10 
            y = i^2
            z += y
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    global_scope = scoped_tree.topscope
    outer_scope = global_scope.children[1]
    for_scope = outer_scope.children[1]
    @test outer_scope.kind == :hard
    @test for_scope.kind == :soft
    @test Set([:i, :y]) == for_scope.symbols
    @test Set([:x, :z]) == outer_scope.symbols

    i = scoped_tree.root_node[1,2,3,1,1]
    @test scoped_tree.identifier_to_scope[i] == for_scope

    i2 = scoped_tree.root_node[1,2,3,2,1,2,1]
    @test scoped_tree.identifier_to_scope[i] == for_scope

    y = scoped_tree.root_node[1,2,3,2,1,1]
    @test scoped_tree.identifier_to_scope[y] == for_scope

    z = scoped_tree.root_node[1,2,3,2,2,1]
    @test scoped_tree.identifier_to_scope[z] == outer_scope



    source_code = """
    function greet()
        x = "hello" # new local
        println(x)
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    
    global_scope = scoped_tree.topscope
    greet_scope = global_scope.children[1]
    @test Set([:greet]) == global_scope.symbols
    @test Set([:x]) == greet_scope.symbols


    source_code = """
    x = 123
    function greet()
        x = "hello" # new local
        println(x)
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)

    global_scope = scoped_tree.topscope
    greet_scope = global_scope.children[1]
    @test Set([:greet, :x]) == global_scope.symbols
    @test Set([:x]) == greet_scope.symbols

    source_code = """
    function A()
        x = 0
        function B()
            while x < 10
                x += 1
            end
        end
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)


    global_scope = scoped_tree.topscope
    A_scope = global_scope.children[1]
    B_scope = A_scope.children[1]
    while_scope = B_scope.children[1]
    x = while_scope.node[1,1]
    @test find_innermost_scope_for_node(global_scope, x) == while_scope
    @test scoped_tree.identifier_to_scope[x] == A_scope
    x = while_scope.node[2,1,1]
    @test find_innermost_scope_for_node(global_scope, x) == while_scope
    @test scoped_tree.identifier_to_scope[x] == A_scope


    source_code = """
    function A()
        function B()
            A()
        end
        B()
    end
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)


    global_scope = scoped_tree.topscope
    A_scope = global_scope.children[1]
    B_scope = A_scope.children[1]
    B = A_scope.node[2,2,1]
    @test scoped_tree.identifier_to_scope[B] == A_scope
    A = B_scope.node[2,1,1]
    @test scoped_tree.identifier_to_scope[A] == global_scope

    source_code = "[x for x in 1:10]"
    syntax_tree = get_syntax_tree_for_str(source_code)
    scoped_tree = get_scoped_tree(syntax_tree)
    global_scope = scoped_tree.topscope

    @test :x in global_scope.children[1].symbols
    @test length(global_scope.children[1].definitions) == 1

    source_code = """
    function A()
        x = 0
        function B()
            x = 1
        end
        B()
        x # == 1
    end
    """
    source_code = """
    function A()
        x = 0
        function B(x)
            x = 1
        end
        B(x)
        x # == 0
    end
    """

    source_code = """
    function A()
        x = 0
        let x = 1
            x = 2
        end
        x # == 0
    end
    """
    # syntax_tree = get_syntax_tree_for_str(source_code)
    # scoped_tree = get_scoped_tree(syntax_tree)

    # global_scope = scoped_tree.topscope
end

# print_scope_tree(global_scope)