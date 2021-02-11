import re
import sys
sys.path.insert(0, "../textToLatex")
from pytexit import py2tex

supported_operators = ["**", "/", "*", "+", ">", "<", "="]
supported_word_operators = ["sqrt", "abs", "inf"]
replace = {"⋅" : "*", "−" : "-", "^" : "**", "𝑥" : "x", "𝑎" : "a", "𝑏" : "b", "𝑦" : "y", "–": "-", "≥" : ">=", "≤": "<=", "∪" : "U"}
conditionally_replace = {"[" : "(", "]" : ")"}
regex = re.compile("|".join(map(re.escape, replace.keys())))

#Figure out way to deal with equal signs
def preprocess_text_to_latex(text, tutoring=False, stepMC= False):
    text = str(text)
    text = regex.sub(lambda match: replace[match.group(0)], text)
    if not re.findall("[\[|\(][-\d\s\w]+,[-\d\s\w]+[\)|\]]", text): #Checking to see if there are coordinates/intervals before replacing () with []
        text = regex.sub(lambda match: conditionally_replace[match.group(0)], text)
    
    
    #Account for space in sqrt(x, y)
    text = re.sub(r"sqrt[\s]?\(([^,]+),[\s]+([^\)])\)", r"sqrt(\g<1>,\g<2>)", text)
    text = re.sub(r"sqrt(?:\s*)?\(", r"sqrt(", text)
    text = re.sub(r"abs(?:\s*)?\(", r"abs(", text)
    text = re.sub("\([\s]*([-\d]+)[\s]*,[\s]*([-\d]+)[\s]*\)", "(\g<1>,\g<2>)", text) #To account for coordinates
    for operator in supported_operators:
        text = re.sub("(\s?){0}(\s?)".format(re.escape(operator)), "{0}".format(operator), text)
        
    words = text.split()
    latex = False
    for i in list(range(len(words))):
        word = words[i]
        
        if any([op in word for op in supported_operators]) or any([op in word for op in supported_word_operators]):
            punctuation = re.findall("[\?\.,:]", word) #Capture all the punctuation at the end of the sentence
            if punctuation:
                punctuation = punctuation[0]
            else:
                punctuation = ""
            word = re.sub("[\?\.,:]", "", word)
            try:                
                sides = re.split('(=|U|<=|>=)', word)
                sides = [handle_word(side) for side in sides]
                new_word = ""
                if tutoring and stepMC:
                    new_word = "$$" + "".join(sides) + "$$"
                    #sides = ["$$" + side + "$$" for side in sides] 
                elif tutoring:
                    new_word = "$$" + "".join(sides) + "$$"
                    # new_word = "$$" + "".join([side.replace("\\", "\\\\") for side in sides]) + "$$"
                    #sides = ["$$" + side.replace("\\", "\\\\") + "$$" for side in sides]
                else:
                    new_word = "<InlineMath math=\"" + "".join(sides) + "\"/>"
                    #sides = ["<InlineMath math=\"" + side + "\"/>" for side in sides]
                #new_word = "=".join(sides)
                new_word += punctuation
                latex=True
                words[i] = new_word
                
            except Exception as e:
                print("This failed")
                print(word)
                print(e)
                pass
    text = " ".join(words)
    return text, latex

def handle_word(word):
    latex_dic = {"=": "=", "U": " \cup ", "<=" : " \leq ", ">=" : " \geq "}
    if word in latex_dic:
        return latex_dic[word]
    
    coordinates = re.findall("[\(|\[][-\d\s]+,[-\d\s]+[\)|\]]",word)
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
    word = py2tex(word, simplify_output=False)
    
    #Here do the substitutions for the things that py2tex can't handle
    for item in scientific_notation:
        word = re.sub(item[0] + "\{" + item[1] + "\}", item[0] + "\\\\times {" + item[1] + "}", word)
    word = re.sub(r"\\operatorname{pm}\\left\(a\\right\)(\\times)?", r"\\pm ", word)
    
    return word[2:-2]