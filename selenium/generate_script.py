import re

def generate_script_arithmetic(selector, answer):
    answer = re.sub(r'\\', r'\\\\', answer)
    answer = re.sub('\'', '\\\'', answer)
    answer = re.sub('\$', '', answer)
    selector = re.sub(r"\"", "\\\"", selector)
    script = "document = new Document();\n"
    script += "ans = document.evaluate(\"{}\", document, null, 9, null).singleNodeValue;\n".format(selector)
    script += "var MQ = MathQuill.getInterface(2);\n"
    script += "mathField = MQ.MathField(ans);\n"
    script += "mathField.focus();\n"
    script += "mathField.latex(\"\");\n"
    script += "mathField.write('{}');\n".format(answer)
    return script

