
@testset "Turing" begin
    
    source_code = "@model function func() end"
    st = get_syntax_tree_for_str(source_code)
    preprocess_syntaxtree!(Turing(), st)
    node = st.root_node
    func = node[1]
    @test is_model(Turing(), func)
    @test get_model_name(Turing(), func) == :func


    source_code = "
    @model function test(y, z)
        x ~ Normal(0., 1.)
        y ~ Gamma(1, 1)
        i = 1
        z[i] ~ Bernoulli(0.5)
        e[i] ~ Bernoulli(0.5)
    end
    "
    st = get_syntax_tree_for_str(source_code)
    preprocess_syntaxtree!(Turing(), st)
    node = st.root_node
    
    func = node[1]
    @test is_model(Turing(), func)

    func_body = func[2,2]

    x_def = func_body[1]
    y_def = func_body[2]
    z_def = func_body[4]
    e_def = func_body[5]

    
    dist_node = get_distribution_node(Turing(), VariableDefinition(x_def))
    @test sourcetext(dist_node) == "Normal(0., 1.)"
    dist_name, dist_params = get_distribution(Turing(), dist_node)
    @test dist_name == "Normal"
    @test sourcetext(dist_params["location"]) == "0."
    @test sourcetext(dist_params["scale"]) == "1."

    for (def, name, is_obs) in [(x_def,:x,false), (y_def,:y,true), (z_def,Symbol("z[i]"),true), (e_def,Symbol("e[i]"),false)]
        @test is_random_variable_definition(Turing(), def)
        variable = VariableDefinition(def)
        @test get_random_variable_name(Turing(), variable) == name
        @test is_observed(Turing(), variable) == is_obs
    end

    source_code = """
    @model function test(y, z)
        x ~ Uniform()
    end
    """
    st = get_syntax_tree_for_str(source_code)
    preprocess_syntaxtree!(Turing(), st)
    node = st.root_node
    
    func_body = node[1,2,2]
    x_def = func_body[1]
    dist_node = get_distribution_node(Turing(), VariableDefinition(x_def))
    @test_throws ErrorException get_distribution(Turing(), dist_node)
    
end