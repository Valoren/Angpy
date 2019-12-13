import record

def test_applyValues():
    source = {1: {2: [3, 4]}, 5: [6, 7]}
    dest = {1: {2: [8, 9]}, 5: [11, 12]}
    record.applyValues(source, dest, overwriteKeys = [1])
    assert repr(dest[1]) == repr(source[1])
    assert repr(dest[5]) == repr([11, 12, 6, 7])
    dest = {1: {2: [8, 9]}, 5: [11, 12]}
    record.applyValues(source, dest, overwriteKeys = [2])
    assert repr(dest[1]) == repr(source[1])
    dest = {1: {2: [8, 9]}, 5: [11, 12]}
    record.applyValues(source, dest)
    assert repr(dest[1][2]) == repr([8, 9, 3, 4])
    assert repr(dest[5]) == repr([11, 12, 6, 7])

