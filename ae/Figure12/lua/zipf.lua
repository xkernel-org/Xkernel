-- zipf.lua — Deterministic Zipf(1.2) access pattern for wrk2
--
-- Used by Figure 12 to generate NGINX requests following a Zipf distribution.
-- Each thread gets a unique, deterministic seed for reproducibility.

local total_files = 100
local zipf_alpha = 1.2
local base_seed = 42

local counter = 1
function setup(thread)
   thread:set("id", counter)
   counter = counter + 1
end

function init(args)
   math.randomseed(base_seed + id)
   math.random(); math.random(); math.random()
end

local function get_zipf_index(n, alpha)
    local r = math.random()
    local index = math.floor(math.pow(r, -1/alpha))
    if index > n then
        return math.random(1, n)
    else
        return index
    end
end

request = function()
   local index = get_zipf_index(total_files, zipf_alpha)
   local path = "/bench/file_" .. index .. ".bin"
   return wrk.format("GET", path)
end
