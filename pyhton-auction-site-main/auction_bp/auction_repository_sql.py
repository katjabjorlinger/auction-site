""" ansvarar för CRUD till databasen för Items """

import os.path
import sqlite3

from .auction_item import Item

""" repo initieras"""
class ItemRepository:
    def __init__(self, file_name: str):
        self.file_name = file_name
        # initierar databas och skapar om den inte redan finns
        if not os.path.exists(self.file_name):
            self.__init_item_sqlite()

    """ get all  hämtar alla föremål från databasen """
    def get_all(self) -> list:
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT items.*, categories.name AS category_name
        FROM items
        LEFT JOIN categories ON items.category_id = categories.id
        ''')
        item_records = cursor.fetchall()

        #returnerar en lista med alla items
        items = []
        for record in item_records:
            item = Item(*record[:-1]) 
            item.category = record [-1]
            items.append(item)

        conn.close()
        return items

    """ lägger till ett nytt föremål """
    def add(self, item: Item):
        conn= sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO items (id, titel, description, seller, price, image, start_time, end_time, likes, dislikes, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item.id, item.titel, item.description, item.seller, item.price, item.image, item.start_time, item.end_time, 0, 0, item.category_id))

        conn.commit()
        conn.close()

    """ tar bort ett föremål """
    def delete(self, id: str) -> bool:
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        # raderar föremålet med matchande id 
        cursor.execute('DELETE FROM items WHERE id = ?', (id,))

        conn.commit()
        conn.close()
        return True

    """ uppdaterar ett föremål """
    def update(self, item: Item):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        # insert med uppdaterade värden
        cursor.execute('''
                UPDATE items
                SET titel = ?, description = ?, seller = ?, price = ?, image = ?, start_time = ?, end_time = ?
                WHERE id = ?
            ''', (item.titel, item.description, item.seller, item.price, item.image, item.start_time, item.end_time, item.id))

        conn.commit()
        conn.close()

    """ hitta ett föremål baserat på id """
    def find_by_id(self, id: str) -> Item:
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM items WHERE id = ?', (id,))
        item_record = cursor.fetchone()

        conn.close()

        #returnerar föremålet med matchande id
        if item_record:
            item = Item(*item_record)
            return item
        else:
            return None

    """ hämtar föremål i en vald kategori """
    def get_items_by_category(self, category: str) -> list:

        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT items.*, categories.name AS category_name
            FROM items
            LEFT JOIN categories ON items.category_id = categories.id
            WHERE categories.name = ?
        ''', (category,))

        item_records = cursor.fetchall()
        items = []
        for record in item_records:
            item = Item(*record[:-1]) # Exkluderar category_name i konstruktor
            item.category_name = record[-1] #Lägger till category_name manuellt
            items.append(item)

        conn.close()
        return items

    """ hämtar alla kategorier """
    def get_all_categories(self) -> list:

        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories')
        categories = [row[0] for row in cursor.fetchall()]
        conn.close ()
        return categories

    """ like increment med 1 """
    def increment_likes(self):
        self.likes += 1

    """ dislike ökar med 1 """
    def increment_dislikes(self):
        self.dislikes += 1

    """ ökar antalet likes för ett föremål """
    def increment_likes_for_item(self, item_id):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        # Hämtar nuvarande antal gillningar för ett objekt
        cursor.execute('SELECT likes FROM items WHERE id = ?', (item_id,))
        current_likes = cursor.fetchone()

        if current_likes is not None:
            new_likes = current_likes[0] + 1  # Öka antalet likes
            cursor.execute('UPDATE items SET likes = ? WHERE id = ?', (new_likes, item_id))
            conn.commit()

        conn.close()

    """ antal dislikes """
    def increment_dislikes_for_item(self, item_id):
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        # Hämtar nuvarande antal ogillanden för ett objekt
        cursor.execute('SELECT dislikes FROM items WHERE id = ?', (item_id,))
        current_dislikes = cursor.fetchone()

        if current_dislikes is not None:
            new_dislikes = current_dislikes[0] + 1  # Öka antalet dislikes
            cursor.execute('UPDATE items SET dislikes = ? WHERE id = ?', (new_dislikes, item_id))
            conn.commit()

        conn.close()

    """ sökfunktion """
    def search_items(self, search_term: str) -> list:
        conn = sqlite3.connect(self.file_name)
        cursor = conn.cursor()

        # söker efter auktioner med hjälp av like där titel eller beskrivning innehåller sökordet
        cursor.execute('''
            SELECT * FROM items
            WHERE titel LIKE ? OR description LIKE ?
        ''', ('%' + search_term + '%', '%' + search_term + '%'))

        item_records = cursor.fetchall()

        items = []
        for record in item_records:
            item = Item(*record)
            items.append(item)

        conn.close()
        return items
    
    """ skapa tabell om den inte redan existrerar """
    def __init_item_sqlite(self):
            if not os.path.exists(self.file_name):
                # kopplar till databasen
                conn = sqlite3.connect(self.file_name)
                cursor = conn.cursor()

                # skapar tabellen items
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS items (
                        id TEXT,
                        titel TEXT,
                        description TEXT,
                        seller TEXT,
                        price REAL,
                        image TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        likes INTEGER DEFAULT 0,
                        dislikes INTEGER DEFAULT 0,
                        category_id INTEGER

                    )
                ''')

                # lista med exempelföremål
                sample_items = [
                    (
                        "1111",
                        "Sommarkväll vid sjön",
                        "En stämningsfull och romantisk oljemålning som fångar en stilla sommarkväll vid en spegelblank sjö. Tavlan utmärks av sitt mjuka ljus och sina levande detaljer – från de dansande solstrålarna över vattenytan till de gröna trädkronorna som ramar in scenen. Anna Larsson, känd för sina naturnära landskap, kombinerar här realism och impressionistiska penseldrag för att skapa en harmonisk atmosfär.Tavlan är i gott skick med mindre spår av ålder i färglagret. Levereras med en elegant, tidstypisk guldram.",
                        "Elin Johansson",
                        75000.0,
                        "https://historly.se/cdn/shop/products/790SummerEvening.jpg?v=1631366774",
                        "2025-01-15 12:00:00",
                        "2025-01-27 12:00:00",
                        10,
                        2,
                        1
                    ),

                    (
                        "1112",
                        "Kvinna i sommargrönska",
                        "Originalmålning av en svensk konstnär. Signerad I. Svensson i nedre vänstra hörnet. En drömsk och färgstark målning föreställande en kvinna som står omgiven av lummig sommargrönska. Hennes vita klänning kontrasterar vackert mot de djupa gröna nyanserna i bakgrunden, där solens strålar silas genom trädkronorna. Motivet andas stillhet och eftertanke, med subtila drag av nordisk romantik som är kännetecknande för Ingrid Svenssons konstnärliga uttryck. Den mjuka, nästan impressionistiska tekniken förstärker känslan av en varm sommardag, och konstnären fångar naturens lekfulla ljus och skuggspel på ett mästerligt sätt.Tavlan är i mycket gott skick och ramas in av en elegant, klassisk träram som ytterligare lyfter verket.",
                        "Emma Svensson",
                        5000.0,
                        "https://images.auctionet.com/thumbs/hd_item_3990260_3587a62f27.jpg",
                        "2025-01-01 09:00:00",
                        "2025-01-15 21:00:00",
                        20,
                        0,
                        1
                        ),

                    (
                        "1114",
                        "Porträtt",
                        "Originalmålning av den svenska konstnären Karin Holm (1912–1975). Signerad K. Holm i nedre högra hörnet. Ett elegant och gåtfullt porträtt av en kvinna i en blå klänning. Konstnären använder mjuka penseldrag och subtila skuggor för att skapa en intim och harmonisk stämning. Den blå färgskalan dominerar och förstärker verkets drömska kvalitet. Karin Holm är känd för sitt skickliga sätt att framhäva mänskliga uttryck och känslor genom färger och komposition. Tavlan är i gott skick och inramad i en diskret silverfärgad ram som lyfter fram motivet.",
                        "Peter Karlsson",
                        8000.0,
                        "https://th.bing.com/th/id/OIP.ij6uj9vsqmKHGbKpLj9jWAHaJQ?w=203&h=254&c=7&r=0&o=5&pid=1.7",
                        "2025-01-03 09:00:00",
                        "2025-01-10 21:00:00",
                        10,
                        0,
                        1
                    ),

                    (
                        "1116",
                        "Antikt flygelpiano",
                        "Ett vackert antikt flygelpiano från 1900-talets början, tillverkat av det välkända märket Bechstein. Pianot är i mörkbetsat trä med vackra detaljer och originalben i klassisk stil. Ljudet är varmt och fylligt, med en resonans som passar både professionella musiker och entusiaster. Tangenterna är i gott skick och mekaniken fungerar utan problem, men en stämning rekommenderas. Perfekt för både spel och som dekorativt inslag i hemmet.",
                        "Anders Petersson",
                        70000.0,
                        "https://th.bing.com/th/id/OIP.aj3F1I1nQnwAfYqQsOl3swAAAA?w=179&h=180&c=7&r=0&o=5&pid=1.7",
                        "2025-01-01 09:00:00",
                        "2025-02-27 21:00:00",
                        50,
                        0,
                        2
                    ),

                    (
                        "1117",
                        "The Beatles - Abbey Road (Originalpress)",
                        "En originalpress av The Beatles ikoniska album 'Abbey Road' från 1969. Skivan är i mycket gott skick (VG+) och omslaget har endast mindre slitage i kanterna. Ett eftertraktat samlarobjekt för fans av klassisk rock och vinylentusiaster. Albumet innehåller odödliga låtar som 'Come Together' och 'Here Comes the Sun'. Ett måste för alla som uppskattar musikhistoria och kvalitetsmusik.",
                        "Kajsa Karsslon",
                        2000.0,
                        "https://i.ebayimg.com/images/g/jjsAAOSw7tFnYYb1/s-l1600.webp",
                        "2025-01-01 09:00:00",
                        "2025-01-07 21:00:00",
                        15,
                        0,
                        2
                    ),

                    (
                        "1118",
                        "Akustisk gitarr - Martin D-28",
                        "En förstklassig akustisk gitarr av modellen Martin D-28, känd för sitt kristallklara ljud och utmärkta hantverk. Tillverkad av solid sitkagran och palisander, vilket ger en balanserad ton och fantastisk projektion. Gitarren är i mycket gott skick med endast minimala tecken på användning. Perfekt för både professionella musiker och samlare av högkvalitativa instrument. Levereras med original hardcase.",
                        "Bengt Turesson",
                        25000.0,
                        "https://img.kytary.com/eshop_cz/stredni_pdp/na/637080581160000000/07c26032/64696641/martin-d-28-modern-deluxe.avif",
                        "2025-01-01 09:00:00",
                        "2025-02-15 09:00:00",
                        30,
                        0,
                        2
                    ),

                    (
                        "1119",
                        "Snurrfåtölj 70-tal",
                        "En elegant och bekväm snurrfåtölj i tidlös design, klädd i oranget tyg. Fåtöljen kombinerar form och funktion med sin mjukt vadderade sits och ryggstöd, perfekt för avkoppling eller arbete. Den stabila foten i polerad krom möjliggör enkel rotation och ger en stilren touch. Passar lika bra i vardagsrummet som i hemmakontoret. Fåtöljen är i gott skick med endast minimalt slitage. Ett utmärkt val för den som söker komfort och modern estetik.",
                        "Anna Andersson",
                        2000.0,
                        "https://images.auctionet.com/uploads/item_473199_46dc9b03db.JPG",
                        "2025-01-15 09:00:00",
                        "2025-03-20 21:00:00",
                        10,
                        0,
                        3
                    ),

                    (
                        "1120",
                        "Sidobord i natursten",
                        "Ett elegant sidobord med skiva i natursten, perfekt för att tillföra en känsla av lyx och modernitet till hemmet. Bordsskivan är tillverkad av polerad natursten med vackra ådringar som gör varje exemplar unikt. Den stabila metallramen i svart ger en stilren kontrast till stenens naturliga struktur. Bordet är i mycket gott skick och passar utmärkt som avlastningsbord i vardagsrummet, sovrummet eller hallen.",
                        "Elin Karlsson",
                        2500.0,
                        "https://images.auctionet.com/thumbs/large_item_3991020_149f6846b1.jpg",
                        "2025-01-01 09:00:00",
                        "2025-01-30 13:00:00",
                        12,
                        0,
                        3
                    ),

                    (
                        "1121",
                        "Tapetserat skåp från 1950-talet",
                        "Ett unikt och charmigt skåp från 1950-talet, klätt i originaltapet med ett retroinspirerat blommönster. Skåpets klassiska linjer och tidstypiska detaljer gör det till en utmärkt inredningsdetalj för den som uppskattar vintage och skandinavisk design. Insidan erbjuder praktisk förvaring med hyllplan och lådor. Skåpet är i gott skick med mindre tecken på ålder, vilket förstärker dess autentiska karaktär. Ett perfekt tillskott för hemmet som kombinerar historia och funktionalitet.",
                        "Kalle Karlsson",
                        4500.0,
                        "https://images.auctionet.com/thumbs/large_item_3984442_d0f4a8ea70.jpg",
                        "2025-01-01 09:00:00",
                        "2025-03-01 21:00:00",
                        8,
                        0,
                        3
                    ),

                    (
                        "1122",
                        "Vintage kamera - Leica M3",
                        "En klassisk Leica M3-kamera, känd för sin tidlösa design och exceptionella kvalitet. Denna modell, tillverkad på 1950-talet, är en av de mest eftertraktade kamerorna av både samlare och fotografer. Kameran är i mycket gott skick med fullt fungerande mekanik och optik. Objektivet, ett Summicron 50mm f/2, ger skarpa bilder med vacker bokeh. Perfekt för analog fotografering eller som ett exklusivt samlarobjekt. Levereras med original läderfodral.",
                        "Johan Johansson",
                        500.0,
                        "https://images.auctionet.com/thumbs/large_item_3992195_e155bec7dc.jpg",
                        "2025-01-01 09:00:00",
                        "2025-01-12 21:00:00",
                        25,
                        0,
                        4
                    ),

                    (
                        "1123",
                        "Kobra telefon - Retroklassiker",
                        "En ikonisk Kobra-telefon, en tidlös designklassiker från 1950-talet. Tillverkad i svart bakelit med den karakteristiska böjda formen som blivit symbolisk för skandinavisk design. Telefonen är i mycket gott skick för sin ålder med fungerande mekanik och original sladd. Ett perfekt samlarobjekt eller en dekorativ detalj för hemmet som hyllar retrostil.",
                        "Robert Svensson",
                        1200.0,
                        "https://images.auctionet.com/thumbs/large_item_3914489_7b82669cbf.jpg",
                        "2025-01-01 09:00:00",
                        "2025-03-02 21:00:00",
                        18,
                        0,
                        4
                    ),

                    (
                        "1124",
                        "Silverarmband - Vintage",
                        "Ett elegant vintagearmband i sterling silver med detaljerat hantverk. Armbandet har en tidlös design med intrikata mönster och en solid känsla, perfekt som både vardagssmycke och till fest. Stämplat med silvermärkning, vilket garanterar dess äkthet. Armbandet är i mycket gott skick och passar en handled med en diameter upp till cirka 18 cm. Ett klassiskt smycke för den stilmedvetna.",
                        "Johanna Fransson",
                        1500.0,
                        "https://images.auctionet.com/thumbs/large_item_3934424_8b4441d044.jpg",
                        "2025-01-01 09:00:00",
                        "2025-01-21 22:00:00",
                        20,
                        0,
                        5
                    ),

                    (
                        "1125",
                        "Burberry-kappa - Klassisk trenchcoat",
                        "En elegant och tidlös trenchcoat från Burberry, känd för sitt ikoniska rutmönster och högkvalitativa material. Kappan är tillverkad i beige bomull med vattenavvisande yta och knäppning framtill. Designad med klassiska detaljer som stormskydd, justerbara manschetter och ett avtagbart midjebälte. Den typiska Burberry-rutiga fodringen ger en exklusiv touch. Kappan är i mycket gott skick med minimala tecken på användning. Ett stilrent plagg för både vardag och fest.",
                        "Gunnar Einarsson",
                        4500.0,
                        "https://images.auctionet.com/thumbs/medium_item_3991154_639670a9df.jpg",
                        "2025-01-01 09:00:00",
                        "2025-01-14 11:00:00",
                        30,
                        0,
                        6
                    ),

                    (
                        "1126",
                        "Louis Vuitton-handväska - Monogram Canvas",
                        "En exklusiv handväska från Louis Vuitton, tillverkad i det ikoniska Monogram Canvas-materialet med detaljer i läder. Väskan är både stilren och praktisk, med en rymlig interiör och en justerbar axelrem för bekvämlighet. Klassiska detaljer som guldfärgade metalldelar och präglad märkning på lädret förstärker dess lyxiga känsla. Väskan är i mycket gott skick med endast små tecken på användning. Perfekt för den som vill kombinera stil och funktion.",
                        "Urban Turesson",
                        8500.0,
                        "https://images.auctionet.com/thumbs/large_item_3990957_eaa689730a.jpg",
                        "2025-01-01 09:00:00",
                        "2025-03-12 21:00:00",
                        35,
                        1,
                        6
                    ),

                    (
                        "1131",
                        "Damklocka - Cartier Tank Française",
                        "En elegant damklocka från Cartier, modell Tank Française, som kombinerar tidlös design med lyxig känsla. Boetten är tillverkad i rostfritt stål och har en silvervit urtavla med romerska siffror och blå visare. Den ikoniska fyrkantiga formen ger en sofistikerad och modern look. Klockan drivs av ett kvartsurverk och har ett armband i rostfritt stål som avslutas med ett dolt viklås. Klockan är i mycket gott skick och levereras med originalbox och certifikat. Ett perfekt val för den som uppskattar stil och kvalitet.",
                        "Volkan Anderssson",
                        35000.0,
                        "https://images.auctionet.com/thumbs/large_item_3991381_00bc830ba6.jpg",
                        "2025-01-01 09:00:00",
                        "2025-04-14 21:00:00",
                        50,
                        0,
                        7
                    ),

                    (
                        "1133",
                        "Bokserie - Pax Britannia",
                        "En samling av böcker från Pax Britannia. Denna steampunk-inspirerade serie, skriven av Jonathan Green, utspelar sig i ett alternativt Viktorianskt England där teknologi och äventyr möts. Böckerna innehåller spännande berättelser med inslag av action, mysterium och fantastiska världar. Denna samling innehåller flera titlar i serien, alla i gott skick. Ett utmärkt tillfälle för fans av steampunk-genren eller samlare av unika bokserier.",
                        "Carl Jönsson",
                        1200.0,
                        "https://images.auctionet.com/thumbs/large_item_3689846_1627469bd3.jpg",
                        "2025-01-01 09:00:00",
                        "2025-02-20 21:00:00",
                        10,
                        0,
                        8
                    ),

                    (
                        "1134",
                        "Bok - Titanic: The Legend",
                        "En fascinerande bok om Titanic, fylld med historiska fakta, bilder och berättelser om det legendariska fartygets öde. Boken erbjuder en djupgående inblick i Titanic, från dess konstruktion och lyxiga interiör till den tragiska förlisningen och de efterföljande myterna som omger händelsen. Perfekt för historieintresserade och samlare av nautiska memorabilia. Boken är i gott skick och en inspirerande läsning för alla som vill fördjupa sig i en av historiens mest ikoniska berättelser.",
                        "Sven Gunnarsson",
                        350.0,
                        "https://d3tj81smxskx4e.cloudfront.net/WJqe-V_pPJt3OjZQkHPjIbH_ShKidXjjK3fcbtbGZk0/s:768:768/rt:fit/sm:1/scp:1/q:75/fn:1602099-13883182_fullscreen/czM6Ly9hdWt0aW9u/LXByb2R1Y3Rpb24v/aXRlbV9pbWFnZXMv/MTYwMjA5OS8xMzg4/MzE4Ml9vcmlnaW5h/bC5qcGc",
                        "2025-01-01 09:00:00",
                        "2025-03-30 21:00:00",
                        5,
                        0,
                        8
                    )
                ]

                #Insert exempelföremål till tabellen items
                for item in sample_items:
                    cursor.execute('''
                        INSERT INTO items (id, titel, description, seller, price, image, start_time, end_time, likes, dislikes, category_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', item)

                # commit och stänger
                conn.commit()
                conn.close()
