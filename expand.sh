#bash snippet to convert tabs to spaces.
for f in *.py
do  mv $f "$f.old" && expand -t 4 "$f.old" > $f && rm ./*.py.old && rm ./*.py.new
done