import container
import util.id
import util.serializer



## Simple Thing for testing serializations.
class DummyThing:
    def __init__(self):
        self.id = util.id.getId()
        self.funcPointer = None
        self.objectPointer = None
        self.inventory = container.Container()


    def testA(self):
        return "Hello, world! %d" % self.id


    def testB(self):
        return "Goodbye, world! %d" % self.id


    def getSerializationDict(self):
        return {'id': self.id, 
                'funcPointer': self.funcPointer, 
                'objectPointer': self.objectPointer, 
                'inventory': self.inventory}



## Create a bare DummyThing with no details filled in.
def createBareDummy(gameMap):
    return DummyThing()


## Test basic relationships: object references, function pointers, and
# containment. 
def test1():
    util.serializer.registerObjectClass(DummyThing.__name__, createBareDummy)
    thing1 = DummyThing()
    thing2 = DummyThing()
    thing3 = DummyThing()
    thing1.funcPointer = thing2.testA
    thing2.funcPointer = thing1.testB
    thing1.objectPointer = thing2
    thing2.objectPointer = thing1
    thing1.inventory.subscribe(thing2)
    thing1.inventory.subscribe(thing3)

    holder = container.Container(id = 'test1Container')
    holder.subscribe(thing1)
    holder.subscribe(thing2)

    testSerializer = util.serializer.Serializer()
    testSerializer.addContainer(holder)
    testSerializer.addObject(thing3)
    testSerializer.writeFile('test.txt')

    testDeserializer = util.serializer.Deserializer()
    testDeserializer.loadFile('test.txt', None)
    testContainer = testDeserializer.getContainer('test1Container')
    object1 = testDeserializer.getObject(1)
    object2 = testDeserializer.getObject(3)
    object3 = testDeserializer.getObject(5)
    assert(object1 in testContainer)
    assert(object2 in testContainer)
    assert(object3 not in testContainer)
    assert(object1.funcPointer() == 'Hello, world! 3')
    assert(object2.funcPointer() == 'Goodbye, world! 1')
    assert(object1.objectPointer is object2)
    assert(object2.objectPointer is object1)
    assert(object2 in object1.inventory)
    assert(object3 in object1.inventory)


test1()

