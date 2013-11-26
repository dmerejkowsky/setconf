#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# setconf
# Utility for setting options in configuration files.
#
# Alexander Rødseth <rodseth@gmail.com>
#
# GPL2
#
# May 2009
# Dec 2011
# Jan 2012
# Mar 2012
# Jun 2012
# Jul 2012
# Mar 2013
# Jul 2013
# Nov 2013
#

from sys import argv
from sys import exit as sysexit
from os import linesep
from os.path import exists
from tempfile import mkstemp

# TODO: Use optparse or argparse if shedskin is no longer a target.

NL = bytes(linesep, 'UTF-8')
VERSION = "0.6.3"
ASSIGNMENTS = ['==', '=>', '=', ':=', '::', ':']


def firstpart(line, including_assignment=True):
    assert(type(line) == type(bytes()))
    stripline = line.strip()
    if not stripline:
        return None
    # Skip lines that start with #, // or /*
    if stripline.startswith(b'#') or stripline.startswith(b'//') or \
            stripline.startswith(b'/*'):
        return None
    # These assignments are supported, in this order
    assignment = ""
    found = []
    for ass_str in ASSIGNMENTS:
        ass = bytes(ass_str, 'UTF-8')
        assert(type(ass) == type(bytes()))
        if ass in line:
            found.append(ass)
    if len(found) == 1:
        # Only one assignment were found
        assignment = found[0]
    elif found:  # > 1
        # If several assignments are found, use the first one
        firstpos = len(line)
        firstassignment = ""
        for ass in found:
            pos = line.index(ass)
            if pos < firstpos:
                firstpos = pos
                firstassignment = ass
        assignment = firstassignment
    # Return the "key" part of the line
    if assignment:
        if including_assignment:
            return line.split(assignment, 1)[0] + assignment
        else:
            return line.split(assignment, 1)[0]
    # No assignments were found
    return None


def changeline(line, newvalue):
    assert(type(line) == type(bytes()))
    assert(type(newvalue) == type(bytes()))
    first = firstpart(line)
    if first:
        if b"= " in line or b": " in line or b"> " in line:
            return first + b" " + newvalue
        elif b"=\t" in line or b":\t" in line or b">\t" in line:
            return first + b"\t" + newvalue
        else:
            return first + newvalue
    else:
        return line


def test_changeline():
    passes = True
    passes = passes and changeline(b"rabbits = DUMB", b"cool") == b"rabbits = cool"
    passes = passes and changeline(
        b"for ever and ever : never",
        b"and ever") == b"for ever and ever : and ever"
    passes = passes and changeline(
        b"     for  ever  and  Ever   :=    beaver",
        b"TURTLE") == b"     for  ever  and  Ever   := TURTLE"
    passes = passes and changeline(b"CC=g++", b"baffled") == b"CC=baffled"
    passes = passes and changeline(b"CC =\t\tg++", b"baffled") == b"CC =\tbaffled"
    passes = passes and changeline(b"cabal ==1.2.3", b"1.2.4") == b"cabal ==1.2.4"
    passes = passes and changeline(
        b"TMPROOT=${TMPDIR:=/tmp}",
        b"/nice/pants") == b"TMPROOT=/nice/pants"
    passes = passes and changeline(b"    # ost = 2", b"3") == b"    # ost = 2"
    passes = passes and changeline(b" // ost = 2", b"3") == b" // ost = 2"
    passes = passes and changeline(b"  ost = 2", b"3") == b"  ost = 3"
    passes = passes and changeline(b"   /* ost = 2 */", b"3") == b"   /* ost = 2 */"
    passes = passes and changeline(bytes("æøå =>\t123", 'UTF-8'), b"256") == bytes("æøå =>\t256", 'UTF-8')
    print("Changeline passes: %s" % (passes))
    return passes


def changelines(lines, key, value):
    newlines = []
    for line in lines:
        if not line.strip():
            newlines.append(line)
            continue
        firstp = firstpart(line, False)
        if not firstp:
            newlines.append(line)
            continue
        elif firstp.strip() == key:
            newlines.append(changeline(line, value))
        else:
            newlines.append(line)
    return newlines

def changebytes(buf, key, value):
    assert(type(buf) == type(bytes()))
    lines = buf.split(NL)
    newlines = []
    for line in lines:
        if not line.strip():
            newlines.append(line)
            continue
        firstp = firstpart(line, False)
        if not firstp:
            newlines.append(line)
            continue
        elif firstp.strip() == key:
            newlines.append(changeline(line, value))
        else:
            newlines.append(line)
    return newlines

def test_change():
    testcontent = b"""LIGHTS =    ON
bananas= not present
tea := yes
    crazyclown    :ok

"""
    testcontent_changed = b"""LIGHTS = off
bananas= not present
tea := yes
    crazyclown    :ok

"""
    passes = True
    a = b"".join(changebytes(testcontent, b"LIGHTS", b"off"))
    b = b"".join(testcontent_changed.split(NL))
    passes = passes and a == b
    print("Change passes: %s" % (passes))
    return passes


def changefile(filename, key, value, dummyrun=False):
    """if dummyrun==True, don't write but return True if changes would have been made"""
    # Read the file
    try:
        file = open(filename, 'rb')
        data = file.read()
        file.close()
    except IOError:
        print("Can't read %s" % (filename))
        sysexit(2)
    # Change and write the file
    changed_contents = NL.join(changebytes(data, key, value))
    # Only add a final newline if the original contents had one at the end
    #if data.endswith(NL):
    #    changed_contents += NL
    if dummyrun:
        return data != changed_contents
    file = open(filename, "wb")
    file.write(changed_contents)
    file.close()


def addtofile(filename, line):
    """Tries to add a line to a file. UTF-8. No questions asked."""
    # Read the file
    try:
        file = open(filename, 'rb')
        data = file.read()
        lines = data.split(NL)[:-1]
        file.close()
    except IOError:
        print("Can't read %s" % (filename))
        sysexit(2)
    # Change and write the file
    file = open(filename, "wb")
    lines.append(line)
    added_data = NL.join(lines) + NL
    file.write(added_data)
    file.close()


def test_changefile():
    # Test data
    testcontent = b"keys := missing" + NL + bytes("døg = found", 'UTF-8') + NL * 3 + bytes("æøåÆØÅ", 'UTF-8') + NL
    testcontent_changed = b"keys := found" + NL + \
        bytes("døg = missing", 'UTF-8') + NL * 3 + bytes("æøåÆØÅ", 'UTF-8') + NL
    filename = mkstemp()[1]
    # Write the testfile
    file = open(filename, "wb")
    file.write(testcontent)
    file.close()
    # Change the file with changefile
    changefile(filename, b"keys", b"found")
    changefile(filename, bytes("døg", 'UTF-8'), b"missing")
    # Read the file
    file = open(filename, 'rb')
    newcontent = file.read()
    file.close()
    # Do the tests
    passes = True
    passes = passes and newcontent == testcontent_changed
    print("Changefile passes: %s" % (passes))
    return passes


def change_multiline(data, key, value, endstring=NL, verbose=True, searchfrom=0):
    assert(type(data) == type(bytes()))
    assert(type(key) == type(bytes()))
    assert(type(value) == type(bytes()))
    assert(type(endstring) == type(bytes()))
    if key not in data:
        return data
    if (endstring != NL) and (endstring not in data):
        if verbose:
            print("Multiline end marker not found: " + endstring)
        return data
    startpos = data.find(key, searchfrom)
    if endstring in data:
        endpos = data.find(endstring, startpos + 1)
    else:
        endpos = len(data) - 1
    before = data[:startpos]
    between = data[startpos:endpos + 1]

    linestartpos = data[:startpos].rfind(NL) + 1
    line = data[linestartpos:endpos + 1]
    # If the first part of the line is not a key (could be because it's commented out)...
    if not firstpart(line):
        # Search again, from endpos this time
        return change_multiline(data, key, value, endstring, verbose, endpos)

    after = data[endpos + len(endstring):]
    newbetween = changeline(between, value)
    if between.endswith(NL):
        newbetween += NL
    result = before + newbetween + after
    return result


def test_change_multiline():
    passes = True
    # test 1
    testcontent = b"keys := missing" + NL + b"dog = found" + NL * 3
    testcontent_changed = b"keys := found" + NL + b"dog = found" + NL * 3
    a = change_multiline(testcontent, b"keys", b"found")
    b = testcontent_changed
    extracheck = testcontent.replace(b"missing", b"found") == testcontent_changed
    passes = passes and a == b and extracheck
    if not passes:
        print("FAIL1")
    # test 2
    testcontent = bytes('blabla\nOST=(a\nb)\n\nblabla\nÆØÅ', 'UTF-8')
    testcontent_changed = bytes('blabla\nOST=(c d)\n\nblabla\nÆØÅ', 'UTF-8')
    a = change_multiline(testcontent, b"OST", b"(c d)", b")")
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL2")
    # test 3
    testcontent = bytes('bläblä=1', 'UTF-8')
    testcontent_changed = bytes('bläblä=2', 'UTF-8')
    a = change_multiline(testcontent, bytes("bläblä", 'UTF-8'), b"2")
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL3")
    # test 4
    testcontent = b"\n"
    testcontent_changed = b"\n"
    a = change_multiline(testcontent, bytes("blablañ", 'UTF-8'), b"ost")
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL4")
    # test 5
    testcontent = b""
    testcontent_changed = b""
    a = change_multiline(testcontent, bytes("blabla", 'UTF-8'), b"ost")
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL5")
    # test 6
    testcontent = b"a=(1, 2, 3"
    testcontent_changed = b"a=(1, 2, 3"
    a = change_multiline(testcontent, b"a", b"(4, 5, 6)", b")", verbose=False)
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL6")
    # test 7
    testcontent = b"a=(1, 2, 3\nb=(7, 8, 9)"
    testcontent_changed = b"a=(4, 5, 6)"
    a = change_multiline(testcontent, b"a", b"(4, 5, 6)", b")")
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL7")
    # test 8
    testcontent = b"a=(0, 0, 0)\nb=(1\n2\n3\n)\nc=(7, 8, 9)"
    testcontent_changed = b"a=(0, 0, 0)\nb=(4, 5, 6)\nc=(7, 8, 9)"
    a = change_multiline(testcontent, b"b", b"(4, 5, 6)", b")")
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL8")
    # test 9
    testcontent = b"a=(0, 0, 0)\nb=(1\n2\n3\n)\nc=(7, 8, 9)\n\n"
    testcontent_changed = b"a=(0, 0, 0)\nb=(1\n2\n3\n)\nc=(7, 8, 9)\n\n"
    a = change_multiline(testcontent, b"b", b"(4, 5, 6)", b"]", verbose=False)
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL9")
    # test 10
    testcontent = bytes("""
source=("http://prdownloads.sourceforge.net/maniadrive/ManiaDrive-$pkgver-linux-i386.tar.gz"
        "maniadrive.desktop"
        "ñlicense.txt"
        "https://admin.fedoraproject.org/pkgdb/appicon/show/Maniadrive")
md5sums=('5592eaf4b8c4012edcd4f0fc6e54c09c'
         '064639f1b48ec61e46c524ae31eec520'
         'afa5fac56d01430e904dd6716d84f4bf'
         '9b5fc9d981d460a7b0c9d78e75c5aeca')

build() {
  cd "$srcdir/ManiaDrive-$pkgver-linux-i386"
""", 'UTF-8')
    testcontent_changed = bytes("""
source=("http://prdownloads.sourceforge.net/maniadrive/ManiaDrive-$pkgver-linux-i386.tar.gz"
        "maniadrive.desktop"
        "ñlicense.txt"
        "https://admin.fedoraproject.org/pkgdb/appicon/show/Maniadrive")
md5sums=('123abc' 'abc123')

build() {
  cd "$srcdir/ManiaDrive-$pkgver-linux-i386"
""", 'UTF-8')
    a = change_multiline(testcontent, b"md5sums", b"('123abc' 'abc123')", b")", verbose=False)
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL10")
    # test 11
    testcontent = b"x=(0, 0, 0)\nCHEESE\nz=2\n"
    testcontent_changed = b"x=(4, 5, 6)\nz=2\n"
    a = change_multiline(testcontent, b"x", b"(4, 5, 6)", b"CHEESE", verbose=False)
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL11")
    # test 12
    testcontent = b"# md5sum=('abc123')\nmd5sum=('def456')\nmd5sum=('ghi789')\n"
    testcontent_changed = b"# md5sum=('abc123')\nmd5sum=('OST')\nmd5sum=('ghi789')\n"
    a = change_multiline(testcontent, b"md5sum", b"('OST')", b"\n", verbose=False)
    b = testcontent_changed
    passes = passes and a == b
    if not passes:
        print("FAIL12")
    # result
    print("Change multiline passes: %s" % (passes))
    return passes


def changefile_multiline(filename, key, value, endstring=NL):
    # Read the file
    try:
        file = open(filename, 'rb')
        data = file.read()
        file.close()
    except IOError:
        print("Can't read %s" % (filename))
        sysexit(2)
    # Change and write the file
    new_contents = change_multiline(data, key, value, endstring)
    try:
        file = open(filename, "wb")
        file.write(new_contents)
    except:  # UnicodeEncodeError: not supported by shedskin
        #print("codeEncodeError: Can't change value for %s" % (filename))
        print("Can't change value for %s" % (filename))
        sysexit(2)
    # finally is not supported by shedskin
    file.close()


def test_changefile_multiline():
    # Test data
    testcontent = b"keys := missing" + NL + b"dog = found" + NL * 3 + bytes("æøåÆØÅ", 'UTF-8')
    testcontent_changed = b"keys := found" + NL + b"dog = missing" + NL * 3 + bytes("æøåÆØÅ", 'UTF-8')
    filename = mkstemp()[1]
    # Write the testfile
    file = open(filename, "wb")
    file.write(testcontent)
    file.close()
    # Change the file with changefile
    changefile_multiline(filename, b"keys", b"found")
    changefile_multiline(filename, b"dog", b"missing")
    # Read the file
    file = open(filename, "rb")
    newcontent = file.read()
    file.close()
    # Do the tests
    passes = True
    passes = passes and newcontent == testcontent_changed
    print("Changefile multiline passes: %s" % (passes))
    return passes

# Note that this test function may cause sysexit to be called if it fails
# because it calls the main function directly


def test_addline():
    # --- TEST 1 ---
    testcontent = b"MOO=yes" + NL
    testcontent_changed = b"MOO=no" + NL + b"X=123" + NL + \
                          b"Y=345" + NL + b"Z:=567" + NL + \
                          b"FJORD => 999" + NL + b'vm.swappiness=1' \
                          + NL
    filename = mkstemp()[1]
    # Write the testfile
    file = open(filename, "wb")
    file.write(testcontent)
    file.close()
    # Change the file by adding keys and values
    main(["-a", filename, "X", "123"])
    main(["--add", filename, "Y=345"])
    main(["-a", filename, "Z:=567"])
    main(["--add", filename, "FJORD => 999"])
    main(["--add", filename, "MOO", "no"])
    main(["-a", filename, "vm.swappiness=1"])
    main(["-a", filename, "vm.swappiness=1"])
    # Read the file
    file = open(filename, "rb")
    newcontent = file.read()
    file.close()

    # --- TEST 2 ---
    testcontent_changed2 = b"x=2" + NL
    filename = mkstemp()[1]
    # Write an empty testfile
    file = open(filename, "wb+")
    file.close()
    # Change the file by adding keys and values
    main(["-a", filename, "x=2"])
    # Read the file
    file2 = open(filename, "rb")
    newcontent2 = file2.read()
    file2.close()

    # Do the tests
    passes = True
    passes = passes and (newcontent == testcontent_changed)
    passes = passes and (newcontent2 == testcontent_changed2)
    print("Addline passes: %s" % (passes))
    return passes


def tests():
    # If one test fails, the rest will not be run
    passes = True
    passes = passes and test_changeline()
    passes = passes and test_change()
    passes = passes and test_changefile()
    passes = passes and test_change_multiline()
    passes = passes and test_changefile_multiline()
    passes = passes and test_addline()
    if passes:
        print("All tests pass!")
    else:
        print("Tests fail.")


def create_if_missing(filename):
    if not exists(filename):
        f = open(filename, "w")
        f.close()


def main(args=argv[1:], exitok=True):
    if len(args) == 1:
        if args[0] in ["-t", "--test"]:
            tests()
        elif args[0] in ["-h", "--help"]:
            print("setconf " + VERSION)
            print("")
            print("Changes a key in a textfile to a given value")
            print("")
            print("Syntax:")
            print("\tsetconf filename key value [end string for multiline value]")
            print("")
            print("Options:")
            print("\t-h or --help\t\tthis text")
            print("\t-t or --test\t\tinternal self test")
            print("\t-v or --version\t\tversion number")
            print("\t-a or --add\t\tadd the option if it doesn't exist")
            print("\t\t\t\tcreates the file if needed")
            #print("\t-r or --remove\t\tremove the option if it exist")
            print("")
            print("Examples:")
            print("\tsetconf Makefile.defaults NETSURF_USE_HARU_PDF NO")
            print("\tsetconf Makefile CC clang")
            print("\tsetconf my.conf x=42")
            print("\tsetconf PKGBUILD sha256sums \"('123abc' 'abc123')\" ')'")
            print("\tsetconf app.py NUMS \"[1, 2, 3]\" ']'")
            print("\tsetconf -a server.conf ABC 123")
            #print("\tsetconf -r server.conf ABC")
            print("")
        elif args[0] in ["-v", "--version"]:
            print(VERSION)
    elif len(args) == 2:
        # Single line replace ("x=123")
        filename = args[0]
        keyvalue = args[1]
        if "=" in keyvalue:
            key, value = keyvalue.split("=", 1)
            changefile(filename, key, value)
        else:
            sysexit(2)
    elif len(args) == 3:
        if args[0] in ["-a", "--add"]:
            # Single line replace/add ("x 123")
            filename = args[1]
            keyvalue = bytes(args[2], 'UTF-8')

            create_if_missing(filename)

            # Change the file if possible, if not, add the key value
            assignment = None
            for ass_str in ASSIGNMENTS:
                ass = bytes(ass_str, 'UTF-8')
                if ass in keyvalue:
                    assignment = ass
                    break
            if not assignment:
                sysexit(2)
            _, value = keyvalue.split(assignment, 1)
            key = firstpart(keyvalue, False)

            if changefile(filename, key, value, dummyrun=True):
                changefile(filename, key, value)
            else:
                f = open(filename, 'rb')
                data = f.read()
                f.close()
                if keyvalue not in data:
                    addtofile(filename, keyvalue)
        else:
            # Single line replace ("x 123")
            filename = args[0]
            key = args[1]
            value = args[2]
            changefile(filename, key, value)
    elif len(args) == 4:
        if args[0] in ["-a", "--add"]:
            filename = args[1]
            key = bytes(args[2], 'UTF-8')
            value = bytes(args[3], 'UTF-8')

            create_if_missing(filename)

            # Change the file if possible, if not, add the key value
            if changefile(filename, key, value, dummyrun=True):
                changefile(filename, key, value)
            else:
                keyvalue = key + b"=" + value
                f = open(filename, 'rb')
                data = f.read()
                f.close()
                if keyvalue not in data:
                    addtofile(filename, keyvalue)
        else:
            # Multiline replace
            filename = args[0]
            key = args[1]
            value = args[2]
            endstring = args[3]
            changefile_multiline(filename, key, value, endstring)
    else:
        sysexit(1)

if __name__ == "__main__":
    main()
