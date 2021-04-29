#!/bin/sh
set -e
echo "\n[STAGE 1]: Installing python dependencies (This can take 1-2 minutes)"
pip install -q -r ./TerminalScript/requirements.txt
cd TerminalScript

echo "Note: Currently only supports College Algebra sheet."
read -p 'Enter sheet name: ' sheetName

echo "\n[STAGE 2] Running Script. Script warnings (if any) will print below"
python ./process_sheet.py online "1Lp0uGtQsuzxzrm1TSctuZttJRrvaG0E5cwT-75UKZeY" "$sheetName" TRUE FALSE 2>&1

echo "\n[STAGE 3]: Creating index files..."
cd ..
node ./util/indexGenerator.js

echo "\n[STAGE 4]: Running validator. Validator warnings (if any) will print below."
node --experimental-modules .\postScriptValidator.js 

echo "\n[STAGE 5]: Cleaning up directory..."
rm -rf ./OpenStax1