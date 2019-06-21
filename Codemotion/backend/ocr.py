from helpers import *

# recognize text with tesseract


# ignore non-code segments

import keyword as kw
py_wlist = kw.kwlist + ['print']
cpp_wlist = ['alignas', 'alignof', 'and', 'and_eq', 'asm',
		'atomic_cancel', 'atomic_commit', 'atomic_noexcept',
		'auto', 'bitand', 'bitor', 'bool', 'break', 'case',
		'catch', 'char', 'char16_t', 'char32_t', 'class',
		'compl', 'concept', 'const', 'constexpr', 'const_cast',
		'continue', 'decltype', 'default', 'delete', 'do',
		'double', 'dynamic_cast', 'else', 'enum', 'explicit',
		'export', 'extern', 'false', 'float', 'for', 'friend',
		'goto', 'if', 'import', 'inline', 'int', 'long',
		'module', 'mutable', 'namespace', 'new', 'noexcept',
		'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq',
		'private', 'protected', 'public', 'register',
		'reinterpret_cast', 'requires', 'return', 'short',
		'signed', 'sizeof', 'static', 'static_assert',
		'static_cast', 'struct', 'switch', 'synchronized',
		'template', 'this', 'thread_local', 'throw', 'true',
		'try', 'typedef', 'typeid', 'typename', 'union',
		'unsigned', 'using', 'virtual', 'void', 'volatile',
		'wchar_t', 'while', 'xor', 'xor_eq'] + ['cin', 'cout', 'printf']
java_wlist = ['abstract', 'assert', 'boolean', 'break', 'byte', 
			'case', 'catch', 'char', 'class', 'const',
			'continue', 'default', 'do', 'double', 'else',
			'enum',	'extends', 'final', 'finally', 'float',
			'for', 'goto', 'if', 'implements', 'import',
			'instanceof', 'int', 'interface', 'long', 'native',
			'new', 'package', 'private', 'protected', 'public',
			'return', 'short', 'static', 'strictfp', 'super',
			'switch', 'synchronized', 'this', 'throw', 'throws',
			'transient', 'try', 'void', 'volatile',	'while', 'var']


py_big_ws = [word for word in py_wlist if len(word) > 3]
# assert, break, class, continue, elif, else, except, exec,
# finally, from, global, import, lambda, pass, print, raise,
# return, while, with, yield
cpp_big_ws = [word for word in cpp_wlist if len(word) > 3]
java_big_ws = [word for word in java_wlist if len(word) > 3]

py_med_ws = [word for word in py_wlist if len(word) == 3]
# and, def, del, for, not, try
cpp_med_ws = [word for word in cpp_wlist if len(word) == 3]
java_med_ws = [word for word in java_wlist if len(word) == 3]

py_sml_ws = [word for word in py_wlist if len(word) < 3]
# as, if, in, is, or
cpp_sml_ws = [word for word in cpp_wlist if len(word) < 3]
java_sml_ws = [word for word in java_wlist if len(word) < 3]


import re
# test_string = 'if NOT inside a string'

# finds words ("with" keywords)	# see if keeping duplicates is fine
def loose_check(string):
	# finds keywords (anywhere)
	ws = [keyword for keyword in set(py_wlist + cpp_wlist + java_wlist) if keyword in string]
	return flatten([[w for w in string.split() if k in w] for k in ws]) #test_string

# regular (pun intended) check
def check_for_keywords(string):
	# find words (with keyword as prefix)
	ws_re = re.compile(r'\b(' + '|'.join(set(py_wlist + cpp_wlist + java_wlist)) + r')([a-z]*)') # check groups
	return [''.join(w) for w in ws_re.findall(string)]

def strict_check(string):
	# finds keywords (strictly)
	ws_re_strict = re.compile(r'\b(' + '|'.join(set(py_wlist + cpp_wlist + java_wlist)) + r')\b')
	return [word for word in set(py_wlist + cpp_wlist + java_wlist) if word in ws_re_strict.findall(string)]

# print loose_check(test_string)
# print check_for_keywords(test_string)
# print strict_check(test_string)
