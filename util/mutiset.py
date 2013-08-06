from util.debug import D

class mutiset():

    def __init__(self, list=None, key_field=None, count_field=None):
        if list is None:
            self.dic=dict()
            return

        self.dic={i[key_field]:i[count_field] for i in list}
        

    def __iter__(self):
        for k, m in self.dic.items():
            for i in range(m):
                yield k


    def items(self):
        return self.dic.items()

    def add(self, value):
        if value in self.dic:
            self.dic[value]+=1
        else:
            self.dic[value]=1

    def remove(self, value):
        if value not in self.dic:
            D.error("${value} is not in mutiset", {"value":value})

        count=self.dic[value]
        count-=1
        if count==0:
            del(self.dic[value])
        else:
            self.dic[value]=count



    def count(self, value):
        if value in self.dic:
            return self.dic[value]
        else:
            return 0
