# Author: Swapnil wankhede, UID:2023300260

class MacroProcessor:

    # Initializes all macro processing tables and mappings.
    def __init__(self):
        self.MNT = {}              # Macro Name Table {name: {start, end, params}}
        self.MDT = []              # Macro Definition Table
        self.argtab = []           # Argument table
        self.param_index = {}      # parameter mapping

    # Parses comma-separated parameters/arguments into a clean list.
    def _parse_params(self, param_tokens):
        text = " ".join(param_tokens)
        return [p.strip() for p in text.split(",") if p.strip()]


    # ---------------- PASS 1 ----------------
    # Scans source code, identifies macro definitions, and builds MNT + MDT.
    
    def pass1(self, lines):

        i = 0
        while i < len(lines):

            parts = lines[i].strip().split()

            if len(parts) > 1 and parts[1] == "MACRO":

                macro_name = parts[0]
                params = self._parse_params(parts[2:])

                # store parameters
                self.param_index = {}
                pcount = 1
                for p in params:
                    self.param_index[p] = f"?{pcount}"
                    pcount += 1

                start = len(self.MDT)

                # store MACRO line
                self.MDT.append(lines[i].strip())
                i += 1

                # store body until MEND
                while "MEND" not in lines[i]:

                    line = lines[i]

                    # replace parameters with positional
                    for k, v in self.param_index.items():
                        line = line.replace(k, v)

                    self.MDT.append(line.strip())
                    i += 1

                self.MDT.append("MEND")

                end = len(self.MDT) - 1

                self.MNT[macro_name] = {
                    "start": start,
                    "end": end,
                    "params": params,
                }

            i += 1


    # ---------------- PASS 2 ----------------
    # Expands macro calls using MNT/MDT and returns final expanded source.
    def pass2(self, lines):

        expanded = []

        i = 0
        while i < len(lines):
            line = lines[i]

            parts = line.strip().split()

            if len(parts) == 0:
                i += 1
                continue

            # Skip macro definition block in output
            if len(parts) > 1 and parts[1] == "MACRO":
                i += 1
                while i < len(lines) and "MEND" not in lines[i]:
                    i += 1
                i += 1
                continue

            macro_name = parts[0]

            if macro_name in self.MNT:

                args = self._parse_params(parts[1:])

                # build argument table
                self.argtab = [a.strip() for a in args if a.strip()]

                start = self.MNT[macro_name]["start"]
                end = self.MNT[macro_name]["end"]

                for mdt_index in range(start + 1, end):

                    newline = self.MDT[mdt_index]

                    for j in range(len(self.argtab)):
                        newline = newline.replace(f"?{j+1}", self.argtab[j])

                    expanded.append(newline)

            else:
                expanded.append(line.strip())

            i += 1

        return expanded


    # ---------------- PRINT TABLES ----------------
    # Prints MNT and MDT in formatted table form.
    def print_tables(self):

        print("\nMACRO NAME TABLE (MNT)")
        print("-" * 72)
        print(f"{'Idx':<5}{'Macro Name':<15}{'MDT Start':<12}{'MDT End':<10}{'Parameters'}")
        print("-" * 72)
        for idx, (name, meta) in enumerate(self.MNT.items(), start=1):
            params = ", ".join(meta["params"])
            print(f"{idx:<5}{name:<15}{meta['start']:<12}{meta['end']:<10}{params}")
        print("-" * 72)

        print("\nMACRO DEFINITION TABLE (MDT)")
        print("-" * 72)
        print(f"{'Index':<8}{'Card'}")
        print("-" * 72)
        for idx, line in enumerate(self.MDT):
            print(f"{idx:<8}{line}")
        print("-" * 72)

    # Prints the final expanded assembly code with line numbers.
    def print_expanded_code(self, expanded_code):
        print("\nEXPANDED CODE")
        print("-" * 72)
        print(f"{'Line':<8}{'Statement'}")
        print("-" * 72)
        for idx, line in enumerate(expanded_code, start=1):
            print(f"{idx:<8}{line}")
        print("-" * 72)



# ---------------- DRIVER ----------------

file = open("A.ASM")
lines = file.readlines()

mp = MacroProcessor()

# PASS 1
mp.pass1(lines)

mp.print_tables()

# PASS 2
expanded_code = mp.pass2(lines)
mp.print_expanded_code(expanded_code)