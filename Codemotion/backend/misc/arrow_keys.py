# http://stackoverflow.com/questions/22397289/finding-the-values-of-the-arrow-keys-in-python-why-are-they-triples

import sys, tty, termios

class _Getch:
	def __call__(self):
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try:
			tty.setraw(sys.stdin.fileno())
			ch = sys.stdin.read(3)
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		return ch

def get():
	inkey = _Getch()
	while(1):
		k=inkey()
		if k!='': break
	if k=='\x1b[A':
		return "up"
	elif k=='\x1b[B':
		return "down"
	elif k=='\x1b[C':
		return "right"
	elif k=='\x1b[D':
		return "left"
	else:
		return k

def main():
	for i in range(0,2):
		get()

if __name__=='__main__':
	main()