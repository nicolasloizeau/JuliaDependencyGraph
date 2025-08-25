using Pkg.TOML
using ProgressBars
using Downloads
using GraphIO
using GraphIO.GEXF
using MetaGraphs
using Graphs

function download_registry()
    zip_url = "https://github.com/JuliaRegistries/General/archive/refs/heads/master.zip"
    Downloads.download(zip_url, "registry.zip")
    run(`unzip -o registry.zip -d .`)
end

function get_dependencies(package::String)
    letter = uppercase(first(package))
    fname = "General-master/$(letter)/$(package)/Deps.toml"
    deps = []
    if isfile(fname)
        deps_toml = TOML.parsefile(fname)
        for version in keys(deps_toml)
            push!(deps, keys(deps_toml[version])...)
        end
    end
    return unique(deps)
end

function get_dependencies()
    dependencies = Dict{String, Vector{String}}()
    for letter in ProgressBar('A':'Z')
        for package in readdir("General-master/$(letter)")
            if isdir("General-master/$(letter)/$(package)")
                dependencies[package] = get_dependencies(package)
            end
        end
    end
    return dependencies
end


function build_index(dependencies)
    index = Dict{String, Int}()
    for (i, pkg) in enumerate(keys(dependencies))
        index[pkg] = i
    end
    return index
end

function build_graph(dependencies)
    g = MetaGraph()
    index = build_index(dependencies)
    for (pkg, deps) in dependencies
        for dep in deps
            add_edge!(g, index[pkg], index[dep])
        end
    end
    return g
end


dependencies = get_dependencies()
g = build_graph(dependencies)

# TODO : add node titles, save as gexf
