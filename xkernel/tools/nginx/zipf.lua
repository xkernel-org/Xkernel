-- deterministic_zipf.lua

-- 【配置区域】
local total_files = 100
local zipf_alpha = 1.2
local base_seed = 42 -- 宇宙终极答案，或任意固定整数

-- ----------------------------------------------------------------
-- 1. SETUP 阶段：只在测试开始前运行一次
-- 目的：给每个线程分发一个唯一的数字 ID (1, 2, 3...)
-- ----------------------------------------------------------------
local counter = 1
function setup(thread)
   thread:set("id", counter)
   counter = counter + 1
end

-- ----------------------------------------------------------------
-- 2. INIT 阶段：每个线程启动时运行一次
-- 目的：根据线程 ID 设置独立的、固定的随机种子
-- ----------------------------------------------------------------
function init(args)
   -- 关键逻辑：
   -- 线程 1 的种子 = 42 + 1 = 43
   -- 线程 2 的种子 = 42 + 2 = 44
   -- 这样保证了线程间行为不同（避免惊群效应），但每次运行完全一致！
   math.randomseed(base_seed + id)
   
   -- 预热一下随机数生成器（丢弃前几个数），有时 Lua 的第一个随机数不够随机
   math.random()
   math.random()
   math.random()
end

-- ----------------------------------------------------------------
-- 3. REQUEST 阶段：生成请求
-- ----------------------------------------------------------------
local function get_zipf_index(n, alpha)
    -- 使用 math.random()，此刻它已经是确定性的了
    local r = math.random()
    local index = math.floor(math.pow(r, -1/alpha))
    
    if index > n then 
        -- 如果越界，用确定性的随机回退
        return math.random(1, n) 
    else 
        return index 
    end
end

request = function()
   local index = get_zipf_index(total_files, zipf_alpha)
   
   -- 路径：/bench/file_X.bin
   local path = "/bench/file_" .. index .. ".bin"
   
   return wrk.format("GET", path)
end