

import Sockets
import JSONRPC
import JSON

include("server_endpoints.jl")

is_disconnected_exception(err) = false
is_disconnected_exception(err::InvalidStateException) = err.state === :closed
is_disconnected_exception(err::Base.IOError) = true
is_disconnected_exception(err::CompositeException) = all(is_disconnected_exception, err.exceptions)

ccall(:jl_exit_on_sigint, Nothing, (Cint,), 0)

function jsonrpc_run(x::JSONRPC.JSONRPCEndpoint)
    x.status == :idle || error("Endpoint is not idle.")

    x.write_task = @async try
        try
            for msg in x.out_msg_queue
                if isopen(x.pipe_out)
                    JSONRPC.write_transport_layer(x.pipe_out, msg)
                else
                    break
                end
            end
        catch err
            # added
            if err isa Base.IOError
                # do nothing, remote closed connection
                # @warn "Caught IOError"
            else
                rethrow()
            end
        finally
            close(x.out_msg_queue)
        end
    catch err
        bt = catch_backtrace()
        if x.err_handler !== nothing
            x.err_handler(err, bt)
        else
            Base.display_error(stderr, err, bt)
        end
    end

    x.read_task = @async try
        while true
            message = JSONRPC.read_transport_layer(x.pipe_in)

            if message === nothing || x.status == :closed
                break
            end

            message_dict = JSON.parse(message)

            if haskey(message_dict, "method")
                try
                    put!(x.in_msg_queue, message_dict)
                catch err
                    if err isa InvalidStateException
                        break
                    else
                        rethrow(err)
                    end
                end
            else
                # This must be a response
                id_of_request = message_dict["id"]

                channel_for_response = x.outstanding_requests[id_of_request]
                put!(channel_for_response, message_dict)
            end
        end
        
        close(x.in_msg_queue)

        for i in values(x.outstanding_requests)
            close(i)
        end

        x.status = :closed
    catch err
        bt = catch_backtrace()
        if x.err_handler !== nothing
            x.err_handler(err, bt)
        else
            Base.display_error(stderr, err, bt)
        end
    end

    x.status = :running
end

begin
    mkpath(".pipe")
    pipename = "./.pipe/julia_rpc_socket"
    rm(pipename, force=true)

    server = Sockets.listen(pipename) # creates a socket
    @info "Started Julia Language Server" server
    begin
        try
            while true
                connection = Sockets.accept(server)
                println("Hello ", connection)
        
                connection_endpoint = JSONRPC.JSONRPCEndpoint(connection, connection)

                @info "Run" 
                # run(connection_endpoint)
                jsonrpc_run(connection_endpoint)
                # println("Status: ", connection_endpoint.status)
                
                msg = nothing

                try
                    msg_dispatcher = ServerEndpoints.get_dispatcher()

                    while isopen(connection)
                        # println("Get next message.")
                        msg = JSONRPC.get_next_message(connection_endpoint)
                        println("msg: ", msg["method"])
                        try
                            JSONRPC.dispatch_msg(connection_endpoint, msg_dispatcher, msg)
                        catch err
                            @error "Internal Error" exception=(err, catch_backtrace())
                            JSONRPC.send_error_response(connection_endpoint, msg, -32000, "Server error", string(err))
                        end
                    end
                catch err
                    if !isopen(connection) && is_disconnected_exception(err)
                        empty!(ServerEndpoints._SESSION)
                        @info "Remote closed the connection."
                    end
                finally
                    @info "Close connection"
                    close(connection)
                end
            end
        catch err
            if err isa InterruptException
                @info "Interrupt server."
            else
                rethrow()
            end
        finally   
            @info "Close server."
            close(server)
        end
    end    
end