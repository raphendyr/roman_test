def render_lc(file_, line, col, num_lines=5, print_file=True):
    out = []
    with open(file_) as f:
        lines = f.read().splitlines()
    if print_file:
        out.append("file '%s':" % (file_,))
    if num_lines >= 0:
        ident = len(str(line))
        fmt = "%%%dd: %%s" % (ident,)
        start = max(line - num_lines, 0)
        for i, l in enumerate(lines[start:line+1], start):
            out.append(fmt % (i, l))
        out.append("%s^" % (" "*(col+ident+2),))
    else:
        end = min(line - num_lines, len(lines) - 1)
        ident = len(str(end))
        fmt = "%%%dd: %%s" % (ident,)
        out.append(fmt % (line, lines[line]))
        out.append("%s^" % (" "*(col+ident+2),))
        for i, l in enumerate(lines[line+1:end+1], line+1):
            out.append(fmt % (i, l))
    return out
