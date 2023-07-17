
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
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    func_body = node[2,2]
    @test is_model(Gen(), node)

    x_def = func_body[1]
    @test get_random_variable_node(Gen(), VariableDefinition(x_def)) == x_def[2,1,1,1]
    @test sourcetext(get_program_variable_node(Gen(), VariableDefinition(x_def))) == "x" 
    y_def = func_body[2]
    @test get_random_variable_node(Gen(), VariableDefinition(y_def)) == y_def[1,1,1]
    @test get_program_variable_node(Gen(), VariableDefinition(y_def)).val == :_
    z_def = func_body[4]
    @test get_random_variable_node(Gen(), VariableDefinition(z_def)) == z_def[1]
    @test sourcetext(get_program_variable_node(Gen(), VariableDefinition(z_def))) == "z" 
    e_def = func_body[5]
    f_def = func_body[6]
    @test kind(get_random_variable_node(Gen(), VariableDefinition(f_def))) == K"string"
    @test get_program_variable_node(Gen(), VariableDefinition(f_def)).val == :_
    g_def = func_body[7]
    @test sourcetext(get_random_variable_node(Gen(), VariableDefinition(g_def))) == "h" 
    @test sourcetext(get_program_variable_node(Gen(), VariableDefinition(g_def))) == "g" 


    dist_node = get_distribution_node(Gen(), VariableDefinition(x_def))
    @test sourcetext(dist_node) == "normal(0., 1.)"
    dist_name, dist_params = get_distribution(Gen(), dist_node)
    @test dist_name == "Normal"
    @test sourcetext(dist_params["location"]) == "0."
    @test sourcetext(dist_params["scale"]) == "1."

    for (def, name, is_obs) in [(x_def,:x,false), (y_def,:y,true), (z_def,:z,true), (e_def,Symbol(":e => i"),true), (f_def,Symbol("\"f\""),true)]
        @test is_random_variable_definition(Gen(), def)
        variable = VariableDefinition(def)
        @test get_random_variable_name(Gen(), variable) == name
        @test is_observed(Gen(), variable) == is_obs
    end



    source_code = """
    @gen function test(x)
        for i in eachindex(x)
            {:y => i} ~ normal(0, 1)
            {:z => i} ~ bernoulli(0.5)
        end
    end
    x = [1,2,3]
    observations = choicemap()
    for x in eachindex(x)
        observations[:y => i] = 0.
        observations[:z=>i] = 1
    end
    """
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    func_body = node[2,2]
    

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
    node = JuliaSyntax.parseall(SyntaxNode, source_code)[1]
    func_body = node[2,2]
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
