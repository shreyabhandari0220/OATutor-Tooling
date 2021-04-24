import re
import sys
sys.path.insert(0, "../textToLatex")
from pytexit import py2tex
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

supported_operators = ["**", "/", "*", "+", ">", "<", "=", "_"]
supported_word_operators = ["sqrt", "abs(", "inf", "log{", "ln{"]
answer_only_operators = ["-"]
replace = {"⋅" : "*", "−" : "-", "^" : "**", "𝑥" : "x", "𝑎" : "a", "𝑏" : "b", "𝑦" : "y", "–": "-", "≥" : ">=", "≤": "<=", "∪" : "U", "π" : "pi"}
conditionally_replace = {"[" : "(", "]" : ")"}
regex = re.compile("|".join(map(re.escape, replace.keys())))

#Figure out way to deal with equal signs
def preprocess_text_to_latex(text, tutoring=False, stepMC=False, stepAns=False, render_latex="TRUE"):
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
        text = re.sub(r"@{(\d+|\w+)}", r"aaa\g<1>ttt", text)

        # for operator in supported_operators:
        #     text = re.sub("(\s?){0}(\s?)".format(re.escape(operator)), "{0}".format(operator), text)


    words = text.split()
    latex = False
    angle_bracket = False
    for i in list(range(len(words))):
        word = words[i]
        if render_latex and (((stepMC or stepAns) and \
            any([op in word for op in answer_only_operators])) or \
            any([op in word for op in supported_operators]) or \
            any([op in word for op in supported_word_operators])):
            if not re.findall("[\[|\(][-\d\s\w/]+,[-\d\s\w/]+[\)|\]]", word): # only add in space if is not coordinate
                word = re.sub(",(\S)", ", \g<1>", word)

            punctuation = re.findall("[\?\.,:]", word) #Capture all the punctuation at the end of the sentence
            if punctuation:
                punctuation = punctuation[0]
            else:
                punctuation = ""
            strip_punc = not re.findall("[\d]\.[\d]", word) and not re.findall("[\[|\(][-\d\s\w/]+,[-\d\s\w/]+[\)|\]]", word)
            quote = False
            open_braces = closing_braces = False
            # if the word is wrapped in quote.
            if (word[:2] == "\\\"" and word[-2:] == "\\\"") or (word[0] == "\\\'" and word[-1] == "\\\'"):
                word = word[2:-2]
                quote = True
            # if the word contains 
            if strip_punc:
                word = re.sub("[\?\.,:]", "", word)
            # handles braces in LaTeX
            if word[:1] == "{":
                open_braces = True
                word = word[1:]
            if word[-1:] == "}" and "ln{" not in word:
                closing_braces = True
                word = word[:-1]
            try:                
                sides = re.split('(=|U|<=|>=)', word)
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
                print("This failed")
                print(word)
                print(e)
                pass
    text = " ".join(words)
    text = re.sub(r"\\\\slash\\\\", "/", text)
    text = re.sub(r"aaa(\w+|\d+)ttt", r"@{\g<1>}", text)
    # text = re.sub(r"\n", r"\\\\n", text)
    return text, latex

def handle_word(word):
    latex_dic = {"=": "=", "U": " \cup ", "<=" : " \leq ", ">=" : " \geq "}
    if word in latex_dic:
        return latex_dic[word]
    
    if not (any([op in word for op in supported_operators]) or any([op in word for op in supported_word_operators])):
        return word

    if "log{" in word:
        return re.sub("log{(\d+|\w+)}", r"\\log_{\g<1>}", word)

    if "ln{" in word:
        return re.sub("ln{", r"\\ln{", word)
    
    coordinates = re.findall("[\(|\[][-\d\s\D]+,[-\d\s\D]+[\)|\]]",word)
    if coordinates:
        word = re.sub("inf", r"\\infty", word)
        return word
    
    word = re.sub("\+/-", "pm(a)", word)
    
    original_word = word
    scientific_notation = re.findall("\(?([\d]{2,})\)?\*([\d]{2,})\*\*", word)
    word = re.sub(":sqrt", ": sqrt", word)
    square_roots = re.findall(r"sqrt\(([^,]*)\,([^\)]*)\)", word)
    word = re.sub(",", "", word)
    for root in square_roots:
        word = re.sub(r"sqrt\("+root[0]+root[1]+"\)", r"sqrt("+root[0]+","+root[1]+")", word)
    #word = re.sub(r"sqrt\(([^,]*)\,([^\)]*)\)", r"sqrt(\g<1>:\g<2>)", "sqrt(2, 3)")
    word = re.sub(r"([\w])(\(+[\w])", "\g<1>*\g<2>", word)
    word = re.sub(r"(\)+)([\w])", "\g<1>*\g<2>", word)
    word = re.sub(r"(\))(\()", "\g<1>*\g<2>", word)
    word = re.sub(r"([0-9]+)([a-zA-Z])", "\g<1>*\g<2>", word)
    #word = re.sub( r"([a-zA-Z])(?=[a-zA-Z])" , r"\1*" , word)
    word = re.sub(r"sqrt\*", r"sqrt", word)
    word = re.sub(r"abs\*", r"abs", word)
    word = re.sub(r"pm\*", r"pm", word)
    word = re.sub('\(\-', '(negneg', word)

    word = py2tex(word, print_latex=False, print_formula=False, simplify_output=False)
    
    #Here do the substitutions for the things that py2tex can't handle
    for item in scientific_notation:
        word = re.sub(item[0] + "\{" + item[1] + "\}", item[0] + "\\\\times {" + item[1] + "}", word)
    word = re.sub(r"\\operatorname{(\w*|\d*)pm}\\left\(a\\right\)(\\times)?", r"\g<1>\\pm ", word)
    word = re.sub(r"negneg(\d|\w)", r"\\left(-\g<1>\\right)", word) #handles first negative sign following opening parenthesis
    
    return word[2:-2]