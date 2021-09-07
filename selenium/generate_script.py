import re

def generate_script(selector, answer):
    selector = re.sub(r"\"", "\\\"", selector)
    script = "document = new Document();\n"
    script += "ans = document.evaluate(\"{}\", document, null, 9, null).singleNodeValue;\n".format(selector)
    script += "var MQ = MathQuill.getInterface(2);\n"
    script += "mathField = MQ.MathField(ans);\n"
    script += "mathField.typedText('{}');\n".format(answer)
    return script

# script2 = generate_script(ans2_selector, "sqrt13")
# script2 += "mathField.keystroke('Right');\n"
# script2 += "mathField.typedText('^2');\n"
# script2 += "mathField.keystroke('Right');\n"
# script2 += "mathField.typedText('/25');"