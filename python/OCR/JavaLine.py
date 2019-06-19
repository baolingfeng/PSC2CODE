import Levenshtein
import copy
from java_tokenizer import *
from lm import JAVA_WORDS, JAVA_LINE_STRUCTURE


class JavaLine:
    def __init__(self):
        self.tokens = []

    def __init__(self, input, pos=None):
        if type(input) == str or type(input) == unicode:
            try:
                self.tokens = list(tokenize(input, ignore_errors=True))
            except Exception as e:
                print 'error:', input
                self.tokens = []
            
        elif type(input) == list:
            self.tokens = input
        else:
            print 'unsupported input type', type(input)

        self.pos = pos
        self.init()

    def get_token_type(self, t):
        # cls_type = type(t).__name__
        if isinstance(t, Identifier):
            if t.value in ["String"]:
                token_type = t.value
            elif t.value[0].isupper():
                token_type = "IDU"
            else:
                token_type = "IDL"
        elif isinstance(t, (Keyword, Modifier, BasicType, Separator, Operator, Annotation)):
            token_type = t.value
        elif isinstance(t, (Integer, FloatingPoint, DecimalInteger)):
            token_type = "NUMBER"
        else:
            # constant value including String, boolean, null, char
            token_type = type(t).__name__

        return token_type

    def clean(self):
        self.tokens = [token for token in self.tokens if not (isinstance(token, Identifier) and token.value == "I")]
        
        N = len(self.tokens) - 1
        if N > 0 and self.tokens[N].value in ['|', '1', 'I', '||', 'T', 'i']:
            self.tokens = self.tokens[:N]

    def init(self):
        self.clean()

        self.token_types = []
        for t in self.tokens:
            token_type = self.get_token_type(t)
            self.token_types.append(token_type)

        self.line = self.reformat_tokens().encode("utf8")
        self.line_nospace = self.reformat_tokens_without_space().encode("utf8")
        self.struct = ' '.join(self.token_types)

    def correct(self, correct_words, incorrect_words):
        new_tokens = []
        for tid, token in enumerate(self.tokens):
            new_token = copy.deepcopy(token)
            if isinstance(token, (Separator, Operator, Annotation)):
                new_tokens.append(new_token)
                continue

            if isinstance(token, (Integer, FloatingPoint, DecimalInteger)):
                new_tokens.append(new_token)
                continue

            w = new_token.value.encode("utf8")
            if w in incorrect_words:
                candidates = sorted([w2 for w2 in correct_words if Levenshtein.ratio(
                    w, w2) > 0.8 and Levenshtein.distance(w, w2)<=3], key=lambda x: Levenshtein.distance(x, w))
                
                if len(candidates) > 0:
                    new_token.value = candidates[0]
            
            new_tokens.append(new_token)
        
        return JavaLine(new_tokens, self.pos)
        

    def get_words(self):
        words = []
        for tid, token in enumerate(self.tokens):
            if isinstance(token, (Separator, Operator, Annotation)):
                continue

            if isinstance(token, (Integer, FloatingPoint, DecimalInteger, String)):
                continue

            words.append(token.value)
        return words

    def has_correct_struct(self):
        if self.struct not in JAVA_LINE_STRUCTURE:
            return False

        if "String" in self.token_types:
            if self.line_nospace.count('"') % 2 != 0:
                return False

        return True

    def reset_token(self, tid, value):
        self.tokens[tid].value = value
        self.line = self.reformat_tokens().encode("utf8")
        self.line_nospace = self.reformat_tokens_without_space().encode("utf8")

    def reset_tokens(self, tokens):
        self.tokens = tokens
        self.line = self.reformat_tokens().encode("utf8")
        self.line_nospace = self.reformat_tokens_without_space().encode("utf8")


    def incorrect_words(self, incorrect_words):
        words = []
        for tid, token in enumerate(self.tokens):
            if isinstance(token, (Separator, Operator, Annotation)):
                continue

            if isinstance(token, (Integer, FloatingPoint, DecimalInteger)):
                continue

            if token.value in incorrect_words:
                words.append((tid, token.value))

        return words
        

    def is_incorrect(self, word_set=JAVA_WORDS):
        if self.struct not in JAVA_LINE_STRUCTURE:
            return True

        incorrects = set(
            [w for w in self.get_filtered_words() if w not in word_set])
        if len(incorrects) > 0:
            return True

        if "String" in self.token_types:
            if self.line_nospace.count('"') % 2 != 0:
                return True

        return False

    def get_filtered_words(self, filter_list=(Separator, Operator, Annotation, Integer, FloatingPoint, DecimalInteger, String, Character)):
        return [token.value for token in self.tokens if not isinstance(token, filter_list)]

    def reformat_tokens(self):
        ident_last = False
        output = list()
        for token in self.tokens:
            if token.value in [',', ';', ':']:
                output.append(token.value + ' ')
            elif isinstance(token, (Literal, Keyword, Identifier)):
                if ident_last:
                    output.append(' ')
                output.append(token.value)
            elif isinstance(token, Operator):
                output.append(' ' + token.value + ' ')
            else:
                output.append(token.value)

            ident_last = isinstance(token, (Literal, Keyword, Identifier))

        return ''.join(output)

    def reformat_tokens_without_space(self):
        output = list()
        ident_last = False
        for token in self.tokens:
            if token.value in [',', ';', ':']:
                output.append(token.value + ' ')
            elif isinstance(token, (Literal, Keyword, Identifier)):
                if ident_last:
                    output.append(' ')
                output.append(token.value)
            elif isinstance(token, Operator):
                output.append(token.value)
            else:
                output.append(token.value)

            ident_last = isinstance(token, (Literal, Keyword, Identifier))

        return ''.join(output)

    def __repr__(self):
        return self.line

    def __hash__(self):
        return hash(self.line)

    def __eq__(self, other):
        return self.line == other.line


def main():
    s = 'String b = " monster'
    line = JavaLine(s)
    print line.struct
    print line.get_words()


if __name__ == '__main__':
    main()
