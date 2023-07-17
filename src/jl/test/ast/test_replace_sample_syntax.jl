
@testset "replace_sample_syntax" begin
    source_code = """
    @gen function test()
        x = {:x} ~ normal(0., 1.)
        {:y} ~ gamma(1, 1)
        i = 1
        z ~ bernoulli(0.5)
        {:e => i} ~ Bernoulli(0.5)
        {"f"} ~ Bernoulli(0.5)
    end
    observations = choicemap(:y => 1)
    observations[:z] = 1
    observations[:e => i] = 1
    observations["f"] = 1
    """
    syntax_tree = get_syntax_tree_for_str(source_code)
    replace_sample_syntax!(Gen(), syntax_tree)
    func_body = syntax_tree.root_node[1,2,2]
    x_def = func_body[1]
    y_def = func_body[2]
    z_def = func_body[4]
    e_def = func_body[5]
    f_def = func_body[6]
    @test sprint(show, x_def) == "(= x (call SAMPLE (string \"x\") (call normal 0.0 1.0)))"
    @test sprint(show, y_def) == "(= _ (call OBSERVE (string \"y\") (call gamma 1 1)))"
    @test sprint(show, z_def) == "(= z (call OBSERVE (string \"z\") (call bernoulli 0.5)))"
    @test sprint(show, e_def) == "(= _ (call OBSERVE (string \":e => i\") (call Bernoulli 0.5)))"
    @test sprint(show, f_def) == "(= _ (call OBSERVE (string \"\\\"f\\\"\") (call Bernoulli 0.5)))"


    source_code = "
    @model function test(y, z)
        x ~ Normal(0., 1.)
        y ~ Gamma(1, 1)
        i = 1
        z[i] ~ Bernoulli(0.5)
        e[i] ~ Bernoulli(0.5)
    end
    "
    syntax_tree = get_syntax_tree_for_str(source_code)
    replace_sample_syntax!(Turing(), syntax_tree)

    func_body = syntax_tree.root_node[1,2,2]
    x_def = func_body[1]
    y_def = func_body[2]
    z_def = func_body[4]
    e_def = func_body[5]
    @test sprint(show, x_def) == "(= x (call SAMPLE (string \"x\") (call Normal 0.0 1.0)))"
    @test sprint(show, y_def) == "(= y (call OBSERVE (string \"y\") (call Gamma 1 1)))"
    @test sprint(show, z_def) == "(= (ref z i) (call OBSERVE (string \"z[i]\") (call Bernoulli 0.5)))"
    @test sprint(show, e_def) == "(= (ref e i) (call SAMPLE (string \"e[i]\") (call Bernoulli 0.5)))"
end
