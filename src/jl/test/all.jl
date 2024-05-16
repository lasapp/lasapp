# julia --project=src/jl src/jl/test/all.jl 
using Test

include("../ast/ast.jl")
include("../ppls/ppl.jl")
include("../analysis/analysis.jl")
include("../ppls/ppls.jl")

@testset "Test Julia Language Server" verbose=true begin
    include("ppls/test_turing.jl")
    include("ppls/test_gen.jl")

    include("ast/test_utils.jl")
    include("ast/test_scoped_tree.jl")

    include("analysis/test_cfg.jl")
    include("analysis/test_data_control_flow.jl")
    include("analysis/test_call_graph.jl")
    include("analysis/test_interval_arithmetic.jl")
    include("analysis/test_symbolic.jl")
end
println("Finished testing.")
