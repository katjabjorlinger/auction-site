""" Klass för att representera ett auktionsföremål """


import json
class Item:
    def __init__(self, id, titel, description, seller, price, image, start_time=None, end_time=None, likes=0, dislikes=0, category_id=None, category_name=None):
        #initierar ett nytt objekt för Item

        self.id = id #id för varje item
        self.titel = titel
        self.description = description
        self.seller = seller
        self.price = price #utropspriset
        self.image = image #url för bild
        self.start_time = start_time #tidpunkt när auktionen startar
        self.end_time = end_time #auktionens slut
        self.likes = likes
        self.dislikes = dislikes
        self.category_id = category_id
        self.category_name = category_name

        self.highest_bid = None #föremålets högsta bud
        self.bids = [] #lista med bud 

    #returnerar objeketet som en json string 
    def to_json(self):
            return json.dumps(self.__dict__)

    def __str__(self):
        return self.to_json()
