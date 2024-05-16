
@testset "Gen" begin
    source_code = "@gen function func() end"
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    @test is_model(Gen(), node)
    @test get_model_name(Gen(), node) == :func


    source_code = """
    @gen function test()
        x = {:x} ~ normal(0., 1.)
        {:y} ~ gamma(1, 1)
        i = 1
        z ~ bernoulli(0.5)
        {:e => i} ~ Bernoulli(0.5)
        {"f"} ~ Bernoulli(0.5)
        g = {:h} ~ Bernoulli(0.5)
    end
    observations = choicemap(:y => 1)
    observations[:z] = 1
    observations[:e => i] = 1
    observations["f"] = 1
    """
    st = get_syntax_tree_for_str(source_code)
    preprocess_syntaxtree!(Gen(), st)
    node = st.root_node
    
    func = node[1]
    @test is_model(Gen(), func)
    
    func_body = func[2,2] # block

    x_def = func_body[1]
    @test is_random_variable_definition(Gen(), x_def)
    address_node = get_address_node(Gen(), VariableDefinition(x_def))
    @test kind(address_node) == K"braces" && address_node[1,1].val == :x
    @test string(get_random_variable_name(Gen(), VariableDefinition(x_def))) == ":x"
    @test is_observed(Gen(), VariableDefinition(x_def)) == false

    y_def = func_body[2]
    @test is_random_variable_definition(Gen(), y_def)
    address_node = get_address_node(Gen(), VariableDefinition(y_def))
    @test kind(address_node) == K"braces" && address_node[1,1].val == :y
    @test string(get_random_variable_name(Gen(), VariableDefinition(y_def))) == ":y"
    @test is_observed(Gen(), VariableDefinition(y_def)) == true

    z_def = func_body[4]
    @test is_random_variable_definition(Gen(), z_def)
    address_node = get_address_node(Gen(), VariableDefinition(z_def))
    @test kind(address_node) == K"quote" && address_node[1].val == :z
    @test string(get_random_variable_name(Gen(), VariableDefinition(z_def))) == ":z"
    @test is_observed(Gen(), VariableDefinition(z_def)) == true
    
    e_def = func_body[5]
    @test is_random_variable_definition(Gen(), e_def)
    address_node = get_address_node(Gen(), VariableDefinition(e_def))
    @test kind(address_node) == K"braces" && kind(address_node[1,2]) == K"=>"
    @test is_observed(Gen(), VariableDefinition(e_def)) == true

    f_def = func_body[6]
    @test is_random_variable_definition(Gen(), f_def)
    address_node = get_address_node(Gen(), VariableDefinition(f_def))
    @test kind(address_node) == K"braces" && address_node[1,1].val == "f"
    @test string(get_random_variable_name(Gen(), VariableDefinition(f_def))) == "\"f\""
    @test is_observed(Gen(), VariableDefinition(f_def)) == true

    g_def = func_body[7]
    @test is_random_variable_definition(Gen(), g_def)
    @test g_def[1].val == :g
    @test string(get_random_variable_name(Gen(), VariableDefinition(g_def))) == ":h"
    @test is_observed(Gen(), VariableDefinition(g_def)) == false

    dist_node = get_distribution_node(Gen(), VariableDefinition(x_def))
    @test sourcetext(dist_node) == "normal(0., 1.)"
    dist_name, dist_params = get_distribution(Gen(), dist_node)
    @test dist_name == "Normal"
    @test sourcetext(dist_params["location"]) == "0."
    @test sourcetext(dist_params["scale"]) == "1."

    source_code = """
    @gen function test(x)
        for i in eachindex(x)
            {:y => i} ~ normal(0, 1)
            {:z => i} ~ bernoulli(0.5)
        end
        x ~ bernoulli(0.5)
    end
    x = [1,2,3]
    observations = choicemap()
    for x in eachindex(x)
        observations[:y => i] = 0.
        observations[:z=>i] = 1
    end
    function bla()
        observations[:x] = 1
    end
    """
    st = get_syntax_tree_for_str(source_code)
    preprocess_syntaxtree!(Gen(), st)
    node = st.root_node

    func_body = node[1,2,2]
    y_def = func_body[1,2,1]
    z_def = func_body[1,2,2]
    x_def = func_body[2]

    @test is_random_variable_definition(Gen(), y_def)
    variable = VariableDefinition(y_def)
    @test is_observed(Gen(), variable) == true

    @test is_random_variable_definition(Gen(), z_def)
    variable = VariableDefinition(z_def)
    @test is_observed(Gen(), variable) == true

    @test is_random_variable_definition(Gen(), x_def)
    variable = VariableDefinition(x_def)
    @test is_observed(Gen(), variable) == false
end
