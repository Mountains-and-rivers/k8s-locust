__author__ = "Alex Li"


name = "my \tname is {name} and i am {year} old"

print(name.capitalize())
print(name.count("a"))
print(name.center(50,"-"))
print(name.endswith("ex"))
print(name.expandtabs(tabsize=30))
print(name[name.find("name"):])
print(name.format(name='alex',year=23))
print(name.format_map(  {'name':'alex','year':12}  ))
print('ab23'.isalnum())
print('abA'.isalpha())
print('1A'.isdecimal())
print('1A'.isdigit())
print('a 1A'.isidentifier()) #判读是不是一个合法的标识符
print('33A'.isnumeric())
print('My Name Is  '.istitle())
print('My Name Is  '.isprintable()) #tty file ,drive file
print('My Name Is  '.isupper())
print('+'.join( ['1','2','3'])  )
print( name.ljust(50,'*')  )
print( name.rjust(50,'-')  )
print( 'Alex'.lower()  )
print( 'Alex'.upper()  )
print( '\nAlex'.lstrip()  )
print( 'Alex\n'.rstrip()  )
print( '    Alex\n'.strip()  )
p = str.maketrans("abcdefli",'123$@456')
print("alex li".translate(p) )

print('alex li'.replace('l','L',1))
print('alex lil'.rfind('l'))
print('1+2+3+4'.split('\n'))
print('1+2\n+3+4'.splitlines())
print('Alex Li'.swapcase())
print('lex li'.title())
print('lex li'.zfill(50))

print( '---')

