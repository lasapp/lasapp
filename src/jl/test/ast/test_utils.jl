
@testset "utils" begin
    
    source_code = "function func(x::Int) end"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_function_name(node) == :func

    source_code = "function func(x::Int)::Int end"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_function_name(node) == :func

    source_code = "function Module.func(x::Int) end"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_function_name(node) == :func

    source_code = "function Module.func(x::Int)::Int end"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_function_name(node) == :func


    source_code = "func(x)"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_call_name(node) == :func

    source_code = "Module.func(x)"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_call_name(node) == :func

    source_code = "Vector{Int}(undef, 10)"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_call_name(node) == Symbol("Vector{Int}")

    source_code = "function test(a, b::Int, c=1, d::Int=1; e, f::Int, g=1, h::Int=1) end"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_parameter_names_of_function(node) == [:a, :b, :c, :d, :e, :f, :g, :h]

    source_code = "function test(a, b::Int, c=1, d::Int=1; e, f::Int, g=1, h::Int=1)::Int end"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_parameter_names_of_function(node) == [:a, :b, :c, :d, :e, :f, :g, :h]


    source_code = "x = 1"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_assignment_identifier(node).val == :x

    source_code = "x::Int = 1"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_assignment_identifier(node).val == :x

    source_code = "x[i] = 1"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_assignment_identifier(node).val == :x

    source_code = "x::Vector{Int} = Int[]"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test get_assignment_identifier(node).val == :x

    source_code = "
    1
    x = 1
    function test(a, b::Int, c=1, d::Int=1; e, f::Int, g=1, h::Int=1)::Int
        if a == 1
            y = 2
        else
            x = 3
        end
        for i = b:f
            if i > 10
                break
            end
        end
        while c > 2
            c = c - 1
        end
    end
    "
    syntaxtree = JuliaSyntax.parseall(SyntaxNode, source_code)
    nodefinder = NodeFinder{Bool}(x -> true, x -> get_subnode_for_range(syntaxtree, range(x)) == x; visit_matched_nodes=true)
    result = visit(nodefinder, syntaxtree)
    @test all(result)


    source_code = "x"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test kind(node) == K"Identifier" && is_variable_identifier(node)

    source_code = ":x"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1,1]
    @test kind(node) == K"Identifier" && !is_variable_identifier(node)

    source_code = "Main.x"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1,2,1]
    @test kind(node) == K"Identifier" && is_variable_identifier(node)
    
    source_code = """
    if test1
        A
        B
    else
        C
        if test2
            D
        else
            E
        end
        if test3
            F
        end
    end
    """
    syntaxtree = JuliaSyntax.parseall(SyntaxNode, source_code)

    A = syntaxtree[1,2,1]
    B = syntaxtree[1,2,2]
    C = syntaxtree[1,3,1]
    D = syntaxtree[1,3,2,2,1]
    E = syntaxtree[1,3,2,3,1]
    F = syntaxtree[1,3,3,2,1]

    @test !is_in_different_branch(A,B)
    @test is_in_different_branch(A,C) && is_in_different_branch(A,D) && is_in_different_branch(A,E) && is_in_different_branch(A,F)
    @test !is_in_different_branch(C,F)
    @test is_in_different_branch(D,E)
    @test !is_in_different_branch(D,F)
end
