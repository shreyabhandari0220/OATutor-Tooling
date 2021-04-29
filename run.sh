#!/bin/sh
echo "[STAGE 1]: Installing python dependencies (This can take 1-2 minutes)"
pip install -q -r ./TerminalScript/requirements.txt
cd TerminalScript

echo "[STAGE 2] Running Script. Script warnings (if any) will print below"
python ./process_sheet.py online "1Lp0uGtQsuzxzrm1TSctuZttJRrvaG0E5cwT-75UKZeY" "5.6 Rational Functions" TRUE > /dev/null


echo "[STAGE 2]: Creating index files..."
cd ..
node ./util/indexGenerator.js

echo "[STAGE 3]: Running validator. Validator warnings (if any) will print below."
node --experimental-modules .\postScriptValidator.js 