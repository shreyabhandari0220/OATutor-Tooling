#!/bin/sh
echo "Installing python dependencies... This can take 1-2 minutes."
pip install -q -r ./TerminalScript/requirements.txt
cd TerminalScript
echo "Running Script... Script warnings (if any) will print below"
python ./process_sheet.py online "1Lp0uGtQsuzxzrm1TSctuZttJRrvaG0E5cwT-75UKZeY" "1.1 Real Numbers" TRUE > /dev/null


echo "Installing js dependencies... This can take 1-2 minutes."
cd ..

echo "Creating index files..."
node ./util/indexGenerator.js