# julia --project=src/jl src/jl/test/all.jl 
using Test

import JuliaSyntax: JuliaSyntax, SyntaxNode, @K_str, children, kind, sourcetext, first_byte, last_byte
include("../ppls/ppls.jl")
include("../ast/ast.jl")

include("../analysis/data_control_flow.jl")
include("../analysis/call_graph.jl")
include("../analysis/interval_arithmetic.jl")
include("../analysis/symbolic.jl")


@testset "Test Julia Language Server" verbose=true begin
    include("ppls/test_turing.jl")
    include("ppls/test_gen.jl")

    include("ast/test_utils.jl")
    include("ast/test_scoped_tree.jl")
    include("ast/test_replace_sample_syntax.jl")

    include("analysis/test_data_control_flow.jl")
    include("analysis/test_call_graph.jl")
    include("analysis/test_interval_arithmetic.jl")
    include("analysis/test_symbolic.jl")
end
println("Finished testing.")


# begin
#     function test()
#         x = func()
#         function func()
#             1
#         end
#         x
#     end
#     test()
# end