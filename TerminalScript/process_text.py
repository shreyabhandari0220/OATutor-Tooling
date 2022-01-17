import re
import sys
sys.path.insert(0, "../textToLatex")
from pytexit import py2tex
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

supported_operators = ["**", "/", "*", "+", ">", "<", "=", "_"]
supported_word_operators = ["sqrt", "abs(", "inf", "log{", "ln{", 'log(', 'sum{', '\\theta']
answer_only_operators = ["-"]
replace = {"⋅" : "*", 
            "−" : "-", 
            "^" : "**", 
            "𝑥" : "x", 
            "𝑎" : "a", 
            "𝑏" : "b", 
            "𝑦" : "y", 
            "–": "-", 
            "≥" : ">=", 
            "≤": "<=", 
            "∪" : "U", 
            "π" : "pi"}
conditionally_replace = {"[" : "(", "]" : ")"}
regex = re.compile("|".join(map(re.escape, replace.keys())))
force_latex = 0.0
match = {'(': ')', '{': '}', '[': ']', '\\left(': '\\right)'}

#Figure out way to deal with equal signs
def preprocess_text_to_latex(text, tutoring=False, stepMC=False, render_latex="TRUE", verbosity=False):
    global force_latex
    if render_latex == "TRUE":
        render_latex = True
    else:
        render_latex = False

    if render_latex:
        text = str(text)
        text = regex.sub(lambda match: replace[match.group(0)], text)
        if not re.findall("[\[|\(][-\d\s\w/]+,[-\d\s\w/]+[\)|\]]", text): #Checking to see if there are coordinates/intervals before replacing () with []
            text = regex.sub(lambda match: conditionally_replace[match.group(0)], text)

        #Account for space in sqrt(x, y)
        text = re.sub(r"sqrt[\s]?\(([^,]+),[\s]+([^\)])\)", r"sqrt(\g<1>,\g<2>)", text)
        text = re.sub(r"sqrt(?:\s*)?\(", r"sqrt(", text)
        text = re.sub(r"abs(?:\s*)?\(", r"abs(", text)
        text = re.sub("\([\s]*([-\d]+)[\s]*,[\s]*([-\d]+)[\s]*\)", "(\g<1>,\g<2>)", text) #To account for coordinates
        text = re.sub("\s\\\\\"\s", " ", text) #To account for quoted LaTeX expressions.
        text = re.sub("\\\\pipe", "|", text) #To account for literal | in mc answers
        text = re.sub(r"\\/", r"\\\\slash\\\\", text) #To account for literal /
        text = re.sub(r"@{(\d+|\w+)}", r"aaa\g<1>ttt", text) #For variabilization
        text = re.sub(r"_\{([\w]+),([\w]+)\}", r"_\g<1>\g<2>", text) #To account for subscript in form of A_{i,j} (change to A_ij)

        # for operator in supported_operators:
        #     text = re.sub("(\s?){0}(\s?)".format(re.escape(operator)), "{0}".format(operator), text)

    words = text.split()
    latex = False
    angle_bracket = False
    for i in list(range(len(words))):
        word = words[i]
        if use_latex(word, render_latex):
            if not re.findall("[\[|\(][\+\-\*/\(\)\d\s\w]+,[\+\-\*/\(\)\d\s\w]+[\)|\]]", word): # only add in space if is not coordinate
                word = re.sub(",(\S)", ", \g<1>", word)

            strip_punc = word[-1] in "?.,:"
            quote = False
            open_braces = closing_braces = False
            # if the word is wrapped in quote.
            if (word[:2] == "\\\"" and word[-2:] == "\\\"") or (word[0] == "\\\'" and word[-1] == "\\\'"):
                word = word[2:-2]
                quote = True
            # if the word contains 
            if strip_punc:
                punctuation = word[-1]
                word = word[:-1]
            else:
                punctuation = ""
            # handles braces in LaTeX
            if word[:1] == "{":
                open_braces = True
                word = word[1:]
            if word[-1:] == "}" and "ln{" not in word and "log{" not in word and '/mat' not in word and 'sum{' not in word and '_{' not in word: 
                closing_braces = True
                word = word[:-1]
            # if the word is forced latex
            if word[:2] == '$$' and word[-2:] == '$$':
                word = word[2:-2]
            elif word[:2] == '$$':
                word = word[2:]
            elif word[-2:] == '$$':
                word = word[:-2]
            try:        
                sides = re.split('((?<!\\\\)=|U|<=|>=)', word)
                sides = [handle_word(side) for side in sides]
                new_word = ""
                if tutoring and stepMC:
                    new_word = "$$" + "".join(sides) + "$$"
                else:
                    if quote:
                        new_word = "$$" + "\\\"" + "".join([side.replace("\\", "\\\\") for side in sides]) + "\\\"" + "$$"
                    else:
                        new_word = "$$" + "".join([side.replace("\\", "\\\\") for side in sides]) + "$$"
                    new_word = re.sub(r"\\\\\"\$\$", r"\"$$", new_word)
                    new_word = re.sub(r"\$\$\\\\\"", r"$$\"", new_word)
                if strip_punc:
                    new_word += punctuation
                if open_braces:
                    new_word = "{" + new_word
                if closing_braces:
                    new_word = new_word + "}"
                new_word = re.sub(r"\\operatorname{or}", r"|", new_word)
                latex=True
                words[i] = new_word
                
            except Exception as e:
                if verbosity:
                    print("This failed")
                    print(word)
                    print(e)
                pass
        # if forced verbatim
        if word[:2] == '##' and word[-2:] == '##':
            words[i] = word[2:-2]
        elif word[:2] == '##':
            words[i] = word[2:]
        elif word[-2:] == '##':
            words[i] = word[:-2]
    text = " ".join(words)
    text = re.sub(r"\\\\slash\\\\", "/", text)
    text = re.sub(r"aaa(\w+|\d+)ttt", r"@{\g<1>}", text)
    force_latex = 0.0
    return text, latex

def use_latex(word, render_latex):
    global force_latex
    if word[:2] == '$$' and word[-2:] == '$$':
        force_latex = 0.0
        return True
    if word[:2] == '$$':
        force_latex = True
        return True
    if word[-2:] == '$$':
        force_latex = 0.0
        return True
    if word[:2] == '##' and word[-2:] == '##':
        force_latex = 0.0
        return False
    if word[:2] == '##':
        force_latex = False
        return False
    if word[-2:] == '##':
        force_latex = 0.0
        return False
    if type(force_latex) != float and force_latex:
        return True
    if type(force_latex) != float and not force_latex:
        return False
    if not render_latex:
        return False
    parts = word.split('-')
    for part in parts:
        if any([op in part for op in supported_operators]) or any([op in part for op in supported_word_operators]) and 'info' not in part:
            return True
    return False

def handle_word(word, coord=True):
    latex_dic = {"=": "=", "U": " \cup ", "<=" : " \leq ", ">=" : " \geq "}
    if word in latex_dic:
        return latex_dic[word]

    if r'/mat' in word:
        matches = re.finditer('/mat{.+?}', word)
        for mat in matches:
            word = re.sub(re.escape(mat.group(0)), handle_single_matrix(mat.group(0)), word)
        return word

    if not (any([op in word for op in supported_operators]) or any([op in word for op in supported_word_operators])):
        word = re.sub("𝜃", "\\\\theta", word)
        word = re.sub("°", "\\\\degree", word)
        return word

    if "log{" in word:
        nums = [a.group(1) for a in re.finditer('log\{[^}]+\}\{([^}]+)\}', word)]
        latex_nums = [re.sub(r'\\', r'\\\\', handle_word(n)) for n in nums]
        while re.search('log\{', word):
            word = re.sub('log\{([^}]+)\}\{[^}]+\}', r'\\log_{\g<1>}\\left(' + latex_nums[0] + r'\\right)', word, count=1)
            latex_nums.pop(0)
        return word

    if "ln{" in word:
        return re.sub("ln{", r"\\ln{", word)
        
    coordinates = re.findall("(?<!sqrt)[\(|\[][\+\-\*/\(\)\d\s\D]+,[\+\-\*/\(\)\d\s\D]+[\)|\]]", word)
    if coord and coordinates:
        trailing = ''
        if word[-1] != ')' and word[-1] != ']':
            trailing = word[-1]
            word = word[:-1]
        first = re.search('(\(|\[)([-\d\s\D]+),', word)
        rest = word[word.index(first.group(0)) + len(first.group(0)) - 1:]
        second = re.search(',([-\d\s\D]+)(\)|\])', rest)
        xcoord = handle_word(first.group(2), coord=False)
        ycoord = handle_word(second.group(1), coord=False)
        new_coord = first.group(1) + xcoord + ',' + ycoord + second.group(2) + trailing
        new_coord = re.sub(r'\\', r'\\\\', new_coord)
        return re.sub("[\(|\[][-\d\D]+,[-\d\D]+[\)|\]]", new_coord, word)
    
    word = re.sub("\+/-", "pm(a)", word)
    
    original_word = word
    scientific_notation = re.findall("\(?([\d]{2,})\)?\*([\d]{2,})\*\*", word)
    word = re.sub(":sqrt", ": sqrt", word)
    square_roots = re.findall(r"sqrt\(([^,]*)\,([^\)]*)\)", word)
    word = re.sub(",", "", word)
    for root in square_roots:
        word = re.sub(r"sqrt\("+re.escape(root[0])+re.escape(root[1])+"\)", r"sqrt("+root[0]+","+root[1]+")", word)
    word = re.sub(r"(^ln[\w])(\(+[\w])", "\g<1>*\g<2>", word)
    word = re.sub(r"(\)+)([\w])", "\g<1>*\g<2>", word)
    word = re.sub(r"(\))(\()", "\g<1>*\g<2>", word)
    word = re.sub(r"([0-9]+)([a-zA-Z])", "\g<1>*\g<2>", word)
    word = re.sub(r"sqrt\*", r"sqrt", word)
    word = re.sub(r"abs\*", r"abs", word)
    word = re.sub(r"pm\*", r"pm", word)
    word = re.sub('\*\*\(\-0.', '**(zero', word)
    word = re.sub('\*\*\(\-\.', '**(zero', word) 
    word = re.sub('(?<!(abs)|(log)|(qrt))\(\-', 'negneg(', word)
    word = re.sub(r'\\=', '=', word)
    word = re.sub(r'\'', r"primesymbol", word)
    word = re.sub(r"\\theta", r"theta", word)
    # to handle -(.....) missing parenthesis instance
    while re.search("-\([^\w\d\(]", word):
        open_par_miss = re.search("-\([^\w\d]", word).start() + 1
        close_par_miss = find_matching(word, '(', open_par_miss)
        word = word[:close_par_miss] + '+rightt' + word[close_par_miss + 1:]
        word = word[:open_par_miss] + 'leftt+' + word[open_par_miss + 1:]
    
    sum_match = re.search('sum{([^}]+)}{([^}]+)}{([^}]+)}', word)
    if sum_match:
        sum_var, sum_lower = sum_match.group(1).split('=')
        sum_upper_num = True
        if sum_match.group(2).isnumeric():
            sum_upper = str(int(sum_match.group(2)) + 1)
        else:
            sum_upper = sum_match.group(2)
            sum_upper_num = False
        word = 'sum([' + sum_match.group(3) + ' for ' + sum_var + ' in range(' + sum_lower + ',' + sum_upper + ')])'

    word = py2tex(word, print_latex=False, print_formula=False, simplify_output=False)

    
    #Here do the substitutions for the things that py2tex can't handle
    for item in scientific_notation:
        word = re.sub(item[0] + "\{" + item[1] + "\}", item[0] + "\\\\times {" + item[1] + "}", word)
    word = re.sub(r"\\operatorname{negneg}\\left\(", r"\\left(-", word)
    word = re.sub(r"\\operatorname{invert}", r"\\pm ", word)
    word = re.sub(r"\\operatorname{(\w)}", r"\g<1>", word)
    word = re.sub(r"zero", r"-0.", word)
    word = re.sub("_{2,}", r"\\rule{2cm}{0.15mm}", word)
    word = re.sub('leftt\+', '\\\\left(', word)
    word = re.sub('\+rightt', '\\\\right)', word)
    word = re.sub("primesymbol", "\'", word)
    word = re.sub("°", "\\\\degree", word)
    word = re.sub("𝜃", "\\\\theta", word)
    word = re.sub("θ", "\\\\theta", word)
    word = re.sub("ε", "\\\\varepsilon", word)

    while re.search(r"sqrt\{[^\,]+\,\s*[^\,]+\}", word):
        word = re.sub(r"sqrt\{([^\,]+)\,\s*([^\,]+)\}", r"sqrt[\g<1>]{\g<2>}",  word)

    if sum_match:
        if not sum_upper_num:
            word = re.sub(sum_upper + '-1', sum_upper, word)
    return word[2:-2]

def find_matching(word, char, idx):
    l_count = r_count = 0
    idx += 1
    while idx < len(word):
        if word[idx] == char:
            l_count += 1
        elif word[idx] == match[char]:
            r_count += 1
        if r_count > l_count:
            return idx
        idx += 1
    raise Exception("unmatched" + char)

def handle_single_matrix(mat):
    mat = re.findall('/mat{(.+?)}', mat)[0]
    mat = re.sub(r'\),[\s]*\(', r' \\\\ ', mat)
    mat = re.sub('[\(|\)]', '', mat)
    mat = re.sub('\s*,\s*', ' & ', mat)
    elements = mat.split()
    elements = [re.sub("\\\\", r"\\\\", handle_word(e)) for e in elements]
    mat = ' '.join(elements)
    mat = r"\\begin{bmatrix} " + mat + r" \\end{bmatrix}"
    return mat