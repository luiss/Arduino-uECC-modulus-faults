Import("env")

def post_program_action(source, target, env):
    elf_path = target[0].get_path()
    
    asm_path = elf_path.replace(".elf", ".asm")
    
    objdump_tool = env.subst("$CC").replace("gcc", "objdump").replace("g++", "objdump")
    
    cmd = f'"{objdump_tool}" -S -d -C "{elf_path}" > "{asm_path}"'
    
    print(f"Generating disassembly: {asm_path}")
    env.Execute(cmd)

env.AddPostAction("$BUILD_DIR/${PROGNAME}.elf", post_program_action)
