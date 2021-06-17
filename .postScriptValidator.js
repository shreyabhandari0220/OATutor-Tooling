import problems from './.OpenStax Validator/problemPool.js';

var stepCounter = 0;
var hintCounter = 0;
var errors = 0;
var errorList = {};

var auto = false;
if (process.argv.length > 2 && process.argv[2] == 'auto') {
  auto = true;
}

// node --experimental-modules .\postScriptValidator.js

problems.map(problem => {
  problem.steps.map(step => {
    stepCounter += 1;
    // Check MC answer is one of choices
    if (step.problemType === "MultipleChoice") {
      if (typeof step.choices === 'undefined') {
        if (!auto) {
          console.log("[ERROR] [" + step.id + "] Has no mc options");
          console.log(step);
          console.log("=================");
        }
        errors += 1;
        errorList[step.id] = "Mc question contains no options";
      }
      else if (!step.choices.some(choice => choice === step.stepAnswer[0])) {
        if (!auto) {
          console.log("[ERROR] [" + step.id + "] No mc options match answer verbatim");
          console.log(step);
          console.log("=================");
        }
        errors += 1;
        errorList[step.id] = "No option matches answer verbatim";
      }
    }
    else if (step.problemType === "TextBox") {
      // Check TextBox answers with commas are string type
      if (step.answerType === "arithmetic" && step.stepAnswer[0].search(",") != -1) {
        if (!auto) {
          console.log("[ERROR] [" + step.id + "] Answer type must be string if contains comma.");
          console.log(step);
          console.log("=================");
        }
        errors += 1;
        errorList[step.id] = "Arithmetic answer contains comma";
      }
    }

    step.hints['defaultPathway'].map(hint => {
      hintCounter += 1;
      if (hint.problemType === "MultipleChoice") {
        if (typeof hint.choices === 'undefined') {
          if (!auto) {
            console.log("[ERROR] [" + hint.id + "] Has no mc options");
            console.log(hint);
            console.log("=================");
          }
          errors += 1;
          errorList[hint.id] = "Mc question contains no options";
        }
        else if (!hint.choices.some(choice => choice === hint.hintAnswer[0])) {
          if (!auto) {
            console.log("[ERROR] [" + hint.id + "] No mc options match answer verbatim");
            console.log(hint);
            console.log("=================");
          }
          errors += 1;
          errorList[hint.id] = "No option matches answer verbatim";
        }
      }

      else if (hint.problemType === "TextBox") {
        // Check TextBox answers with commas are string type
        if (hint.answerType === "arithmetic" && hint.hintAnswer[0].search(",") != -1) {
          if (!auto) {
            console.log("[ERROR] [" + hint.id + "] Answer type must be string if contains comma.");
            console.log(hint);
            console.log("=================");
          }
          errors += 1;
          errorList[hint.id] = "Arithmetic answer contains comma";
        }
      }
    })
  })
});
if (!auto) {
  console.log("Validated " + problems.length + " problems, containing " + stepCounter + " steps, and " + hintCounter + " hints.");
  console.log("Found " + errors + " errors.");
}
for (var k in errorList) {
  console.log(k + ": " + errorList[k])
}

//console.log(errorList);