function foo()
    local a = "hello world"
    print(a)
    local function goo()
        print("goo")
    end
    return goo
end 

foo()()

--%%

print(1+3)

