set -x
python houghlines.py 'preview/resources5/frame16412' 'outputs/houghlines1'
python hl-test.py 1 1
python houghlines.py 'preview/resources2/frame3505' 'outputs/houghlines2'
python hl-test.py 2 1
python hl-test.py 2 2
python houghlines.py 'preview/resources2/frame30817' 'outputs/houghlines3'
python hl-test.py 3 1
python hl-test.py 3 2
python hl-test.py 3 3