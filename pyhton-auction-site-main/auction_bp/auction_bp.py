
"""
Hanterar auktionsföremål, budgivning och användarinloggning. Innhåller funktioner
för att skapa, redigera och ta bort föremål, sortera och filtera.
Använder databaser för att lagra föremål, bud och frågor, och inkluderar validering
av inmatningar samt e-postnotifikationer till användare vid budgivning
"""

# Importerar nödvändiga klasser och funktioner från olika moduler
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response, session
from .auction_repository_sql import ItemRepository
from .bid_repository_sql import BidRepository
from .auction_item import Item
from datetime import datetime
from .question_repository_sql import QuestionRepository
from .category_sql import CategoryRepository
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from flask_mail import Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
import json
import re
import random

# Skapar en Blueprint för auktionsrelaterade rutter och funktionalitet
auction_bp = Blueprint('auction_bp', __name__, template_folder="templates")
item_repo = ItemRepository("auction_data.db")
bid_repo = BidRepository("auction_data.db")
question_repo = QuestionRepository("auction_data.db")
category_repo = CategoryRepository("auction_data.db")

# Log in-hantering
login_manager = LoginManager()
login_manager.login_view = 'auction_bp.login'

# E-posthantering
mail = Mail()

# Användarhantering och inloggningsformulär
@login_manager.user_loader
def load_user(user_id):
    # Laddar användardata från en JSON-fil baserat på användarens ID
    with open('users.json', 'r') as f:
        users = json.load(f)
    for user in users:
        if user['id'] == user_id:
            # Returnerar en User-instans om användaren hittas
            return User(user['id'], user['username'], user['password'], user['role'], email=user.get('email'))
    return None

# Definition av User-klass för användarhantering
class User(UserMixin):
    def __init__(self, id, username, password, role, email=None):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.email = email if email else username

# Definierar ett formulär för inloggning med användarnamn och lösenord
class LoginForm(FlaskForm):
    username = StringField('Användarnamn:')
    password = PasswordField('Lösenord:')
    submit = SubmitField('Logga in')

# Inloggningsrutt
@auction_bp.route('/admin', methods=['GET', 'POST'])
def login():
    form = LoginForm() # Skapa ett nytt inloggningsformulär
    if form.validate_on_submit():  # Kontrollera om formuläret är korrekt ifyllt
        # Hämta användarnamn och lösenord från formuläret
        username = form.username.data
        password = form.password.data
        with open('users.json', 'r') as f:
            users = json.load(f) # Ladda användardata från JSON-fil
        # Kontrollera om användarnamn och lösenord matchar en användare
        for user in users:
            if user['username'] == username and user['password'] == password:
                user_obj = User(user['id'], user['username'], user['password'], user['role']) # Skapa en User-instans
                login_user(user_obj)  # Logga in användaren
                return redirect(url_for('auction_bp.get_all_items')) # Om inloggningen lyckas, omdirigera till auktionssidan
    return render_template('admin.html', form=form, loginmessage="Logga in för att kunna ändra eller lägga till auktion")

# Utloggningsrutt
@auction_bp.route('/logout')
@login_required # Säkerställ att användaren är inloggad för att logga ut
def logout():
    logout_user() # Logga ut användaren
    return redirect(url_for('auction_bp.get_all_items'))  # Omdirigera till auktionssidan efter utloggning

# Rutt för att hämta och lista alla auktionsföremål
@auction_bp.route('/', methods=['GET'])
def get_all_items():
    """
    Hämtar alla föremål från databasen och returnerar en HTML-template som listar dessa.
    """
    search = request.args.get('search', '')  # Hämta sökparametern
    sort_by = request.args.get('sort', 'titel')  # Hämta sorteringsparametern, standardvärde är 'titel'
    category = request.args.get('category', '') # Hämta kategoriparametern, standardvärde är ''

    # Hämta alla auktioner eller filtrera med sökning
    if search:
        auctions = item_repo.search_items(search) # Sök efter föremål baserat på söksträng
    elif category:
        auctions = item_repo.get_items_by_category(category) # Hämta föremål baserat på vald kategori
    else:
        auctions = item_repo.get_all() # Hämta alla föremål om ingen filtrering anges

    # Kontrollera om listan är tom och sätt till en tom lista om så är fallet
    if not auctions:
        auctions = []

    # Lägg till högsta bud för varje objekt i listan
    for auction in auctions:
        auction.highest_bid = bid_repo.get_highest_bid_for_item(auction.id) # Hämta högsta bud för varje auktionsobjekt

    # Hämta nuvarande tid för att jämföra datum, utc
    now = datetime.utcnow()

    # Sortera auktionerna baserat på det valda alternativet
    if sort_by == 'titel':
        auctions.sort(key=lambda x: getattr(x, 'titel', '').lower())  # Sortera efter titel (case-insensitive)
    elif sort_by == 'price_asc':
        auctions.sort(key=lambda x: getattr(x, 'price', float('inf'))) # Sortera efter pris i stigande ordning
    elif sort_by == 'price_desc':
        auctions.sort(key=lambda x: getattr(x, 'price', float('-inf')), reverse=True) # Sortera efter pris i fallande ordning

    elif sort_by == 'auction_end':
        auctions.sort(key=lambda x: getattr(x, 'end_time', '')) # Sortera efter slutdatum för auktionen
    elif sort_by == 'ongoing': # Filtrera för att få pågående auktioner
        auctions = [a for a in auctions if a.start_time and a.end_time and datetime.strptime(a.start_time, "%Y-%m-%d %H:%M:%S") <= now and datetime.strptime(a.end_time, "%Y-%m-%d %H:%M:%S") > now]
    elif sort_by == 'completed': # Filtrera för att få avslutade auktioner
        auctions = [a for a in auctions if a.end_time and datetime.strptime(a.end_time, "%Y-%m-%d %H:%M:%S") <= now]
    elif sort_by == 'upcoming': # Filtrera för att få kommande auktioner
        auctions = [a for a in auctions if a.start_time and datetime.strptime(a.start_time, "%Y-%m-%d %H:%M:%S") > now and (not a.end_time or datetime.strptime(a.end_time, "%Y-%m-%d %H:%M:%S") > now) ]

    categories = item_repo.get_all_categories() # Hämta alla kategorier för att kunna visa dem i gränssnittet

    # Skicka filtrerade och sorterade auktioner till templatet
    return render_template("auctions_bp.html", auctions=auctions, sort_by=sort_by, categories=categories, selected_category=category)

#Rutt för att hämta detaljer om ett specifikt auktionsföremål
@auction_bp.route('/details/<id>', methods=['GET'])
def get_item_by_id(id):
    item = item_repo.find_by_id(id)  # Hämta auktionsföremålet baserat på dess ID
    if item:
        item.bids = bid_repo.get_bids_for_item(id) # Hämta alla bud för föremålet
        item.highest_bid = bid_repo.get_highest_bid_for_item(id) # Hämta det högsta budet för föremålet
        item.questions = question_repo.get_questions_for_item(id) # Hämta frågor relaterade till föremålet

        # Kontrollerar om auktionen har startat/avslutats
        now = datetime.now() # Hämta nuvarande tid
        item.has_started = True  # Anta att auktionen har startat
        item.is_finished = False # Anta att auktionen inte är avslutad

        if item.start_time:
            # Om starttiden finns, kontrollera om auktionen har startat
             start_time = datetime.strptime(item.start_time, "%Y-%m-%d %H:%M:%S")
             item.has_started = now >= start_time # Sätt has_started baserat på nuvarande tid

        if item.end_time:
            # Om slutdatum finns, kontrollera om auktionen är avslutad
            end_time = datetime.strptime(item.end_time, "%Y-%m-%d %H:%M:%S")
            item.is_finished = now > end_time # Sätt is_finished baserat på nuvarande tid

         # Rendera HTML-sidan med detaljer för auktionsföremålet
        return render_template("auction_details.html", item=item)

        # Returnera ett felmeddelande om föremålet inte hittas
    return jsonify(message='Item not found'), 404

# Generera ett unikt ID för föremålet
def generate_item_id():
    # Generera ett unikt ID
    item_id = random.randint(1000, 99999)

    # Logga ID:t för att kontrollera
    print(f"Genererat unikt ID: {item_id}")

    # Kontrollera om ID:t är spärrat
    if is_id_blocked(item_id):
        return generate_item_id()  # Generera på nytt om det är spärrat

    return item_id # Returnera det unika ID:t

def is_id_blocked(item_id):
    # Simulerad spärrlogik för ID
    blocked_ids = ["some-blocked-id", "another-blocked-id"] # Lista över spärrade ID:n
    return item_id in blocked_ids # Kontrollera om det givna ID:t finns i listan

# Rutt för att skapa ett nytt auktionsföremål
@auction_bp.route('/', methods=['POST'])
def create_item():
    new_item_data = request.json

    item = item_repo.create_item(new_item_data)  # Skapa föremålet i databasen
    return jsonify(item), 201 # Returnera det skapade föremålet med statuskod 201 (Created)

# Rutt för att visa formuläret för att redigera ett auktionsföremål
@auction_bp.route('/edit/<id>', methods=['GET'])
@login_required
def edit_item_form(id):
    item = item_repo.find_by_id(id)  # Hämta föremålet baserat på dess ID
    categories = category_repo.get_all_categories() # Hämta alla kategorier för att visa i formuläret
    if item:
        return render_template("edititemform.html", item=item, categories=categories) # Rendera redigeringsformuläret med föremålets data och kategorier
    return jsonify(message='Item not found'), 404  # Returnera ett felmeddelande om föremålet inte hittas

# Rutt för att uppdatera ett auktionsföremål
@auction_bp.route('/update', methods=['POST'])
@login_required
def update_item():

    # Hämta värden från formuläret
    title = request.form.get('titel')
    description = request.form.get('description')
    seller = request.form.get('seller')

    # Validering
    if not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', title):
        flash('Titeln måste innehålla minst 2 bokstäver', 'danger')

    if not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', description):
        flash('Beskrivningen måste innehålla minst 2 bokstäver', 'danger')

    if not re.match(r'^[a-zA-ZåäöÅÄÖ ]{2,}$', seller):
        flash('Säljaren måste innehålla minst 2 bokstäver och endast bokstäver', 'danger')

    # Om några felmeddelanden finns, returnera till formuläret utan att skapa föremålet
    if not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', title) or \
       not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', description) or \
       not re.match(r'^[a-zA-ZåäöÅÄÖ ]{2,}$', seller):
        return redirect(url_for('auction_bp.edit_item_form', id=request.form.get('id'))) # Omdirigera tillbaka till redigeringsformuläret

    starttime_value = request.form.get('start_time') # Hämta starttiden från formuläret
    endtime_value = request.form.get('end_time') # Hämta sluttiden från formuläret

    # Konvertera datetime-local till rätt format för databasen
    formatted_starttime = None
    if starttime_value:
        formatted_starttime = datetime.strptime(starttime_value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S") # Formatera starttiden

    # Konvertera datetime-local till rätt format för databasen
    formatted_endtime = None
    if endtime_value:
        formatted_endtime = datetime.strptime(endtime_value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S") # Formatera sluttiden

    # Skapa en ny instans av Item med de uppdaterade värdena
    item = Item(
        request.form.get('id'),
        title,
        description,
        seller,
        request.form.get('price'),
        request.form.get('image'),
        formatted_starttime,
        formatted_endtime
    )
    item_repo.update(item) # Uppdatera föremålet i databasen med de nya värdena
    return redirect(url_for('auction_bp.get_item_by_id', id=item.id)) # Omdirigera till sidan med detaljer för det uppdaterade föremålet

    # Like-funktionalitet
@auction_bp.route('/item/<int:item_id>/like', methods=['POST'])
def like_item(item_id):
    # Öka antalet gillanden för det angivna föremålet
    item_repo.increment_likes_for_item(item_id)
    return redirect(url_for('auction_bp.get_item_by_id', id=item_id))


    # Dislike-funktionalitet
@auction_bp.route('/item/<int:item_id>/dislike', methods=['POST'])
def dislike_item(item_id):
    # Öka antalet ogillanden för det angivna föremålet
    item_repo.increment_dislikes_for_item(item_id)
    return redirect(url_for('auction_bp.get_item_by_id', id=item_id))

# Rutt för att ta bort ett auktionsföremål
@auction_bp.route('/delete/<id>', methods=['DELETE', 'GET'])
@login_required
def delete_item(id):
        if item_repo.delete(id): # Försök att ta bort föremålet från databasen
            flash(f'Auktionen {id} har tagits bort', 'success')
            return redirect(url_for('auction_bp.get_all_items'))
        else:
            return jsonify(message='Item not found'), 404

# Rutt för att visa formuläret för att lägga till ett nytt auktionsföremål
@auction_bp.route('/add', methods=['GET'])
@login_required
def add_item_form():
    categories = category_repo.get_all_categories() # Hämta alla kategorier för att visa i formuläret
    item_id = generate_item_id() # Generera ett unikt ID för det nya föremålet
    return render_template("additemform.html", categories=categories, item_id=item_id) # Rendera formuläret

# Rutt för att lägga till ett nytt auktionsföremål
@auction_bp.route('/add', methods=['POST'])
def add_item():

    # Hämta värden från formuläret
    title = request.form.get('titel')
    description = request.form.get('description')
    seller = request.form.get('seller')

    # Validering
    if not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', title):
        flash('Titeln måste innehålla minst 2 bokstäver', 'danger')

    if not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', description):
        flash('Beskrivningen måste innehålla minst 2 bokstäver', 'danger')

    if not re.match(r'^[a-zA-ZåäöÅÄÖ]{2,}$', seller):
        flash('Säljaren måste innehålla minst 2 bokstäver och endast bokstäver', 'danger')

    # Om några felmeddelanden finns, returnera till formuläret utan att skapa föremålet
    if not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', title) or \
       not re.search(r'[a-zA-ZåäöÅÄÖ].*[a-zA-ZåäöÅÄÖ]', description) or \
       not re.match(r'^[a-zA-ZåäöÅÄÖ]{2,}$', seller):
        return redirect(url_for('auction_bp.add_item_form'))

    # Generera ett unikt ID
    item_id = generate_item_id()

    category_id = request.form.get('category_id') # Hämta kategori-ID från formuläret
    starttime_value = request.form.get('start_time') # Hämta starttid från formuläret
    endtime_value = request.form.get('end_time') # Hämta sluttid från formuläret

    # Konvertera datum
    formatted_starttime = None
    if starttime_value:
        try:
            formatted_starttime = datetime.strptime(starttime_value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S") # Formatera starttiden
        except ValueError as e:
            print("Start date parsing error:", e)
            return redirect(url_for('auction_bp.add_item_form')) #KONTROLLERA HÄR

    # Konvertera datetime-local till rätt format för databasen
    formatted_endtime = None
    if endtime_value:
        try:
            formatted_endtime = datetime.strptime(endtime_value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S") # Formatera sluttiden
        except ValueError as e:
            print("End date parsing error:", e)
            return redirect(url_for('auction_bp.add_item_form')) #KONTROLLERA HÄR

    # Skapa en ny instans av Item med de insamlade värdena
    item = Item(
        item_id,
        title,
        description,
        seller,
        request.form.get('price'),
        request.form.get('image'),
        formatted_starttime,
        formatted_endtime
    )

    item.category_id = category_id # Tilldela kategori-ID:t till föremålet
    item_repo.add(item) # Lägg till det nya föremålet i databasen
    return redirect(url_for('auction_bp.get_all_items')) # Omdirigera till listan över alla auktionsföremål

 #Placera bud
@auction_bp.route('/bid/<id>', methods=['POST'])
@login_required
def place_bid(id):
    """
    Hanterar bud på ett specifikt auktionsobjekt.
    Validerar och sparar budet i databasen.
    """
    # Hämtar användarens namn. Anonym ifall användaren inte är inloggad

    user = current_user.username # Hämta användarens namn (eller anonym om ej inloggad)
    email = current_user.email  # Hämta användarens e-postadress (om registrerad)
    amount = request.form.get('amount') # Hämta budbeloppet från POST-data
    email_outbid = 'email_outbid' in request.form # Kollar om checkboxen är ikryssad
    timestamp = request.form.get('timestamp') # Hämta tidsstämpeln från POST-data

    # Kontrollerar ifall budbeloppet finns
    if not amount:
        flash('Bid amount is required!', 'error')
        return redirect(url_for('auction_bp.get_item_by_id', id=id))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Sätt nuvarande tid som tidsstämpel

    if not timestamp:
        timestamp = datetime.now().isoformat()

    # Konverterar beloppet till ett numeriskt värde
    try:
        amount = float(amount) # Konvertera budbeloppet till ett numeriskt värde
    except ValueError:
        flash('Invalid bid amount!', 'error')
        return redirect(url_for('auction_bp.get_item_by_id', id=id))

    # Hämtar objektet från databasen med id
    item = item_repo.find_by_id(id)

    if not item: # Kontrollerar ifall objektet finns i databasen
        flash('Item not found!', 'error')
        return redirect(url_for('auction_bp.get_all_items'))

    # Kontrollera om auktionen har startat eller avslutats innan budgivning accepteras
    if item.start_time:
        current_time = datetime.now() # Hämta nuvarande tid
        start_time = datetime.strptime(item.start_time, "%Y-%m-%d %H:%M:%S") # Konvertera starttid till datetime-objekt
        if current_time <= start_time: # Kontrollera om auktionen har startat
            flash('This auction has not started yet!', 'error')
            return redirect(url_for('auction_bp.get_item_by_id', id=id))

    if item.end_time:
        current_time = datetime.now()
        end_time = datetime.strptime(item.end_time, "%Y-%m-%d %H:%M:%S")  # Konvertera sluttid till datetime-objekt
        if current_time > end_time: # Kontrollera om auktionen har avslutats
            flash('Auktionen är avslutad.', 'error')
            return redirect(url_for('auction_bp.get_item_by_id', id=id))

    # Kontrollera att budbeloppet är högre än utropspriset
    if amount < item.price:
        flash(f'Ditt bud måste vara högre än utropspriset {item.price} SEK!', 'error')
        return redirect(url_for('auction_bp.get_item_by_id', id=id))

    # Hämta det högsta budet för föremålet
    highest_bid = bid_repo.get_highest_bid_for_item(id)
    if highest_bid is None:
        highest_bid = 0.0 # Sätt högsta budet till 0 om inget bud finns

    # Kontrollera att det nya budet är högre än det högsta budet
    if amount <= highest_bid:
       flash('Ditt bud måste vara högre än det högsta budet!', 'error')
       return redirect(url_for('auction_bp.get_item_by_id', id=id))

    # Skickar alltid en e-postbekräftelse till användaren som lagt budet
    if email:
        msg = Message('Budbekräftelse', sender='din-epost@example.com', recipients=[email]) # Skapa ett e-postmeddelande för bekräftelse
        msg.body = f"Hej {user},\n\nDu har lagt ett bud på {amount} SEK för objektet '{item.titel}'.\n\nLycka till!\nAuktionstorget"
        mail.send(msg) # Skicka e-postmeddelandet

    # Om bevakning är valt, markerar användaren för notifiering
    if email_outbid:
        bid_repo.mark_user_for_outbid_notification(id, user, email)

    # Hämta användare som ska notifieras om de blivit överbudna
    users_to_notify = bid_repo.get_users_to_notify(id)
    print(f"Users to notify: {users_to_notify}")
    for notified_user, notified_email in users_to_notify: # Skicka notifieringar till de användare som ska meddelas om överbud
        if notified_email and notified_email != email:  # Undvik att meddela den senaste budgivaren!
            msg = Message('Du har blivit överbjuden', sender='din-epost@example.com', recipients=[notified_email])
            msg.body = f"Hej {notified_user},\n\nDu har blivit överbjuden på objektet '{item.titel}'.\n\nLägg ett nytt bud för att vinna auktionen!\nAuktionstorget"
            mail.send(msg) # Skicka notifieringsmeddelandet

    # Placerar budet i databasen med id, användare och belopp
    bid_repo.place_bid(id, user, amount, timestamp, email, email_outbid)

    # Visar bekräftelse för den aktuella användaren
    flash(f'Du har lagt ett bud på {int(amount)} kronor på {item.titel}.', 'success')
    return redirect(url_for('auction_bp.get_item_by_id', id=id))

#Rutt för att ta bort bud
@auction_bp.route('/delete_bid/<int:bid_id>', methods=['POST'])
@login_required
def delete_bid(bid_id):
    """
    Tar bort ett bud från databasen baserat på dess ID.
    Kräver att användaren är inloggad.
    """
    try:
        print(f"Försöker ta bort bud med ID: {bid_id}")  # Debug-logg

        if bid_repo.delete_bid(bid_id): # Försök att ta bort budet från databasen
            flash(f'Bud {bid_id} har raderats!', 'success')
        else:
            flash('Budet hittades inte.', 'error')

         # Skicka tillbaka till sidan för det specifika objektet eller alla objekt om ingen ID anges
        item_id = request.args.get('item_id')
        if item_id:
            return redirect(url_for('auction_bp.get_item_by_id', id=item_id))
        return redirect(url_for('auction_bp.get_all_items'))

    except Exception as e:
        print(f"Fel vid borttagning av bud: {e}")
        return redirect(url_for('auction_bp.get_all_items'))


#Frågeformulär
@auction_bp.route('/item/<id>/ask', methods=['POST'])
def ask_question(id):
    user = session.get('username', 'Anonym') # Hämta användarnamn från sessionen (eller anonym om ej inloggad)
    question = request.form.get('question') # Hämta frågan från formuläret

    question_repo.add_question(id, user, question) # Lägg till frågan i databasen kopplad till föremålet
    flash('Din fråga har skickats!', 'success')
    return redirect(url_for('auction_bp.get_item_by_id', id=id))

# Svara på en fråga (admin)
@auction_bp.route('/question/<int:question_id>/answer', methods=['POST'])
@login_required
def answer_question(question_id):
    if current_user.role != 'admin': # Kontrollera att den inloggade användaren är administratör
        flash('Endast administratörer kan svara på frågor.', 'error')
        return redirect(request.referrer)

    answer = request.form.get('answer') # Hämta svaret från formuläret

    question_repo.answer_question(question_id, answer, current_user.username) # Spara svaret i databasen kopplat till frågan
    flash('Frågan har besvarats!', 'success')
    return redirect(request.referrer) # Omdirigera tillbaka till föregående sida
