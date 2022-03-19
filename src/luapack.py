#!/bin/env python3
import argparse
import pathlib
import os, re

included = []

def getRequires(string: str) -> list:
    matches = re.findall(r"require\(.*?\)", string)
    if matches == None: matches = []

    requires = []
    [requires.append(match) for match in matches if match not in requires]

    return requires

def parseRequires(requires: list) -> str:
    preloads = []
    
    for require in requires:
        target = require[len("require(\""):-(len("\")"))]
        if target in included:
            continue

        preload = include(target)
        if not preload:
            if not args.IGNORE_UNKNOWN_PKG:
                print(f"ERROR: Package \"{target}\" couldn't be found.")
                exit(1)
            
            print(f"WARNING: Package \"{target}\" couldn't be found.")

        preloads.append(preload)

    preloadStr = ""
    for preload in preloads:
        preloadStr += f"{preload}\n"

    return preloadStr

def parseTarget(path: pathlib.Path) -> str:
    code = ""
    with open(path.resolve(), "r") as f:
        code = f.read()
        f.close()

    requires = getRequires(code)
    preloads = parseRequires(requires)
    
    return f"""{preloads}
-- {path.name}:
{code}"""

def include(target: str) -> str | None:
    path = target.replace(".", "/") + ".lua"
    if (not os.path.exists(path)) or os.path.isdir(path):
        return False

    included.append(target)

    code = ""
    with open(path, "r") as f:
        code = f.read()
        f.close()

    preloads = parseRequires(getRequires(code))

    return f"""{preloads}
-- {target}:
package.preload['{target}'] = function()
\t{code}
end
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Packages your Lua project into a single .lua file")
    parser.add_argument("-t","--target", help=".lua file which will be packaged", required=True)
    parser.add_argument("--ignore-unknown-pkg", help="Ignores unknown packages", required=False, dest="IGNORE_UNKNOWN_PKG", action="store_true")
    args = parser.parse_args()

    path = pathlib.Path(args.target)
    if (not path.is_file()) or path.is_dir():
        print("bruh")
        exit(1)
    
    packaged = parseTarget(path)
    
    pathlib.Path("build").mkdir(parents=True, exist_ok=True)
    with open(f"build/{path.name}", "w") as f:
        f.write(packaged)
        f.close()
