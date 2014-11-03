


Slicing is Broken in Python 2.7
-------------------------------

###The slice operator in Python2.7 is inconsistent###

At first glance, the python slice operator ```[:]``` is elegant and powerful.
Unfortunately it is inconsistent and forces the programmer to write extra code
to work around these inconsistencies.

    my_list = ['a', 'b', 'c', 'd', 'e']

Let us iterate through some slices:

    my_list[4:] == ['e']
    my_list[3:] == ['d', 'e']
    my_list[2:] == ['c', 'd', 'e']
    my_list[1:] == ['b', 'c', 'd', 'e']
    my_list[0:] == ['a', 'b', 'c', 'd', 'e']

Looks good, but this time let's use negative indices:

    my_list[-4:] == ['b', 'c', 'd', 'e']
    my_list[-3:] == ['c', 'd', 'e']
    my_list[-2:] == ['d', 'e']
    my_list[-1:] == ['e']
    my_list[-0:] == ['a', 'b', 'c', 'd', 'e']  # [] is expected

Using negative idiocies ```[-num:]``` allows the programmer to slice relative to
the right rather than the left.  When ```num``` is a constant this problem is
never revealed, but when ```num``` is a variable, then the inconsistency can
reveal itself.

    def get_suffix(num):
        return my_list[-num:]   # wrong

So, clearly, ```[-num:]``` can not be understood as a suffix slice, rather
something more complicated; especially considering that ```num``` could be
negative.

I advocate never using negative indices in the slice operator.  Rather, use the
```right()``` method instead which is consistent for a range ```num```:

    def right(_list, num):
        if num <= 0:
            return []
        return _list[-num:]


###Python 2.7 ```__getslice__``` is broken###

It would be nice to have our own list-like class that implements slicing in a
way that is consistent.  Specifically, we expect to solve the inconsistent
behaviour seen when dealing with negative indices.

As an example, I would like to ensure my over-sliced-to-the-right and over-
sliced-to-the-left  behave the same.  Let's look at over-slicing-to-the-right,
which behaves as expected on a regular list:

        assert 3 == len(my_list[1:4])
        assert 4 == len(my_list[1:5])
        assert 4 == len(my_list[1:6])
        assert 4 == len(my_list[1:7])
        assert 4 == len(my_list[1:8])
        assert 4 == len(my_list[1:9])

Any slice that requests indices past the list's length is simply truncated.
I would like to implement the same for over-slicing to the left:

        assert 2 == len(my_list[ 1:3])
        assert 3 == len(my_list[ 0:3])
        assert 3 == len(my_list[-1:3])
        assert 3 == len(my_list[-2:3])
        assert 3 == len(my_list[-3:3])
        assert 3 == len(my_list[-4:3])
        assert 3 == len(my_list[-5:3])

Here is an attempt:

    class MyList(list):
        def __init__(self, value):
            self.list = value

        def __getslice__(self, i, j):
            if i < 0:  # CLAMP i TO A REASONABLE RANGE
                i = 0
            elif i > len(self.list):
                i = len(self.list)

            if j < 0:  # CLAMP j TO A REASONABLE RANGE
                j = 0
            elif j > len(self.list):
                j = len(self.list)

            if i > j:  # DO NOT ALLOW THE IMPOSSIBLE
                i = j

            return [self.list[index] for index in range(i, j)]

        def __len__(self):
            return len(self.list)

Unfortunately this does not work.  When the ```__len__``` method is defined,
```__getslice__``` definition changes so that ```i = i % len(self)```: Which
makes it impossible to identify if a negative value is passed to the slice
operator.

The solution is to implement Python's extended slice operator ```[::]```,
which can be implemented using ```__getitem__```; it does not suffer from this
wrap-around problem.


    class BetterList(list):
        def __init__(self, value):
            self.list = value

        def __getslice__(self, i, j):
            raise NotImplementedError

        def __len__(self):
            return len(self.list)

        def __getitem__(self, item):
            if not isinstance(item, slice):
                # ADD [] CODE HERE

            i = item.start
            j = item.stop
            k = item.step

            if i < 0:  # CLAMP i TO A REASONABLE RANGE
                i = 0
            elif i > len(self.list):
                i = len(self.list)

            if j < 0:  # CLAMP j TO A REASONABLE RANGE
                j = 0
            elif j > len(self.list):
                j = len(self.list)

            if i > j:  # DO NOT ALLOW THE IMPOSSIBLE
                i = j

            return [self.list[index] for index in range(i, j)]

[StructList](https://github.com/klahnakoski/pyLibrary/blob/master/pyLibrary/struct.py)
implements slicing this way.
