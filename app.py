from flask import Flask, flash, render_template, request, redirect, url_for
from werkzeug.security import check_password_hash
from db import app, db, User
from flask import jsonify
from db import app, db, User, Progress, Training, TrainingDay, TrainingInhalt
from datetime import timedelta
from datetime import date
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_login import login_user


#neu
app.config['SECRET_KEY'] = 'performfitömerkubi@343'  


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Legen Sie die Route fest, zu der umgeleitet wird, wenn @login_required scheitert

# Route für die Registrierungsseite
@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            error_message = "Benutzername oder E-Mail-Adresse bereits vergeben. Bitte wählen Sie einen anderen."
        else:
            user = User(name=name, email=email, username=username)
            user.set_password(password)

            try:
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect(url_for('fragenkatalog'))
            except Exception as e:
                error_message = "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut."

    return render_template('registration.html', error_message=error_message)

#neu login manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)  # Loggt den Benutzer ein
            return redirect(url_for('dashboard'))
        else:
            return "Falscher Benutzername oder Passwort"

    return render_template('login.html')

#neu logout route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Route für die Startseite
@app.route('/')
def index():
    return render_template('index.html')

# Route für den Fragekatalog
@app.route('/fragenkatalog')
@login_required
def fragenkatalog():
    return render_template('fragenkatalog.html')

# Route für die Verarbeitung des Fragekatalogs
@app.route('/submit_fragenkatalog', methods=['POST'])
@login_required
def submit_fragenkatalog():
    gewicht = request.form.get('gewicht')
    zielgewicht = request.form.get('zielgewicht')

    user = User.query.get(current_user.id)
    user.gewicht = float(gewicht)
    user.zielgewicht = float(zielgewicht)
    db.session.commit()

    return redirect(url_for('dashboard'))


# Route für Workout-Plan
@app.route('/workoutplan', methods=['GET', 'POST'])
@login_required
def workout_plan():

    if request.method == 'POST':
        if 'action' in request.form:
            action = request.form['action']
            
            if action == 'add_training':
                training_name = request.form['training_name']
                if training_name:  # Überprüfung, ob der Name nicht leer ist
                    existing_training = Training.query.filter_by(name=training_name).first()
                    if not existing_training:  # Vermeidung von Duplikaten
                        new_training = Training(name=training_name)
                        db.session.add(new_training)
                        db.session.commit()

            elif action == 'add_to_day':
                day = request.form['day']
                training_id = request.form['training_id']
                if day and training_id:
                    training = Training.query.filter_by(id=training_id).first()
                    if training:
                        new_training_day = TrainingDay(day=day, training_id=training_id, user_id=current_user.get_id())
                        db.session.add(new_training_day)
                        db.session.commit()
            
                        
            elif action == 'reset_week':
                TrainingDay.query.filter_by(user_id=current_user.get_id()).delete()
                db.session.commit()
                
            elif action == 'delete_training':
                training_id = request.form['training_id']
                Training.query.filter_by(id=training_id, user_id=current_user.get_id()).delete()
                db.session.commit()
                
            elif action == 'delete_training_day':
                training_day_id = request.form['training_day_id']
                TrainingDay.query.filter_by(id=training_day_id, user_id=current_user.get_id()).delete()
                db.session.commit()

            elif action == 'edit_training_day':
                training_day_id = request.form.get('training_day_id')
                new_day = request.form.get('day')
                new_training_name = request.form.get('training_name')
                training_day = TrainingDay.query.get(training_day_id)
                training = Training.query.get(training_day.training_id)

                if training_day and training:
                    training_day.day = new_day
                    training.name = new_training_name
                    db.session.commit()

    trainings = Training.query.all()  # Trainings sind allgemein
    training_days = TrainingDay.query.filter_by(user_id=current_user.get_id()).all()  # Trainingstage sind benutzerspezifisch
    return render_template('workoutplan.html', trainings=trainings, training_days=training_days)

#workoutplan add
@app.route('/workoutplan/add', methods=['POST'])
@login_required
def add_training_and_day():
    training_name = request.form['training_name']
    day = request.form['day']
    
    # Überprüfen, ob das Training bereits existiert
    training = Training.query.filter_by(name=training_name).first()
    if not training:
        # Erstellen Sie ein neues Training, wenn es noch nicht existiert
        training = Training(name=training_name)
        db.session.add(training)
        db.session.commit()

    # Training dem Tag zuordnen
    training_day = TrainingDay(day=day, training_id=training.id, user_id=current_user.get_id())
    db.session.add(training_day)
    db.session.commit()

    return redirect(url_for('workout_plan'))


@app.route('/workoutplan/delete', methods=['POST'])
@login_required
def delete_training_or_day():
    # Entfernen der Funktionalität, allgemein zugängliche Trainings zu löschen
    # ...
    
    if 'training_day_id' in request.form:
        # Einen bestimmten Trainingstag löschen
        training_day_id = request.form['training_day_id']
        TrainingDay.query.filter_by(id=training_day_id, user_id=current_user.get_id()).delete()
        db.session.commit()
        flash('Trainingstag erfolgreich gelöscht.', 'success')

    return redirect(url_for('workout_plan'))

#Trainingsinhalt route
@app.route('/trainingsinhalt/<string:day>/<string:training_name>')
@login_required
def trainingsinhalt(day, training_name):
    # Verbesserte Logik zum Abrufen des TrainingDay-Objekts und seiner Trainingsinhalte
    training_day = TrainingDay.query \
        .join(Training, TrainingDay.training_id == Training.id) \
        .filter(TrainingDay.day == day, Training.name == training_name) \
        .filter(TrainingDay.user_id == current_user.get_id()) \
        .first()
    
    if training_day:
        trainingsinhalte = TrainingInhalt.query.filter_by(training_day_id=training_day.id).all()
        # Rendern Sie die Trainingsinhalt-Seite und übergeben Sie die Trainingsinhalte sowie die ID des Trainingstages für das Hinzufügen neuer Inhalte
        return render_template('trainingsinhalt.html', day=day, training_name=training_name, trainingsinhalte=trainingsinhalte, training_day_id=training_day.id)
    else:
        flash('Trainingstag nicht gefunden.', 'danger')
        return redirect(url_for('trainingsinhalt'))  # Leiten Sie um zu einer geeigneten Seite, wenn das Training nicht gefunden wurde


#add trainingsinhalt
@app.route('/add_trainingsinhalt', methods=['POST'])
@login_required
def add_trainingsinhalt():
    training_day_id = request.form.get('training_day_id')
    uebungsname = request.form.get('uebungsname')
    gewicht = request.form.get('gewicht')
    saetze = request.form.get('saetze')
    wiederholungen = request.form.get('wiederholungen')

    # Überprüfung, ob alle Felder ausgefüllt sind
    if not all([training_day_id, uebungsname, gewicht, saetze, wiederholungen]):
        flash('Alle Felder müssen ausgefüllt werden.', 'danger')
        return redirect(request.referrer)
    
    # Überprüfen, ob der TrainingDay dem aktuellen Benutzer gehört
    training_day = TrainingDay.query.filter_by(id=training_day_id, user_id=current_user.get_id()).first()
    if not training_day:
        flash('Trainingstag nicht gefunden oder gehört nicht zum Benutzer.', 'danger')
        return redirect(request.referrer)


    # Versuch, den neuen Trainingsinhalt hinzuzufügen
    try:
        neuer_trainingsinhalt = TrainingInhalt(
        uebungsname=uebungsname,
        gewicht=float(gewicht),
        saetze=int(saetze),
        wiederholungen=int(wiederholungen),
        training_day_id=int(training_day_id),
        user_id=training_day.user_id  # Zuweisung der user_id vom TrainingDay
    )

        db.session.add(neuer_trainingsinhalt)
        db.session.commit()
        flash('Übung erfolgreich hinzugefügt!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Hinzufügen der Übung: {e}', 'danger')
        return redirect(request.referrer)

    # Abrufen des TrainingDay-Objekts, um die Umleitung korrekt durchzuführen
    training_day = TrainingDay.query.get(training_day_id)
    if training_day:
        day = training_day.day
        training_name = training_day.training.name
        return redirect(url_for('trainingsinhalt', day=day, training_name=training_name))
    else:
        flash('Trainingstag nicht gefunden.', 'danger')
        return redirect(url_for('trainingsinahlt'))  # Oder eine andere Seite, die als Fallback dient

#remove trainingsinhalt
@app.route('/remove_trainingsinhalt/<int:inhalt_id>', methods=['POST'])
@login_required
def remove_trainingsinhalt(inhalt_id):
    # Finden Sie den Trainingsinhalt, der gelöscht werden soll
    inhalt = TrainingInhalt.query.filter_by(id=inhalt_id, user_id=current_user.get_id()).first()
    if inhalt:
        try:
            db.session.delete(inhalt)
            db.session.commit()
            flash('Der Trainingsinhalt wurde erfolgreich entfernt.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Es gab ein Problem beim Entfernen des Trainingsinhalts: {}'.format(e), 'danger')
    else:
        flash('Trainingsinhalt nicht gefunden.', 'danger')

    # Leiten Sie den Benutzer zurück zur Seite, von der er gekommen ist
    return redirect(request.referrer)


# Route für Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        user_id = current_user.get_id()
        workout_completed = 'workout' in request.form
        slept_well = 'sleep' in request.form

        # Überprüfen, ob bereits ein Eintrag für heute existiert
        today_progress = Progress.query.filter_by(user_id=user_id, date=date.today()).first()

        # Aktualisieren oder neuen Eintrag erstellen
        if today_progress:
            today_progress.workout_completed = workout_completed
            today_progress.slept_well = slept_well
        else:
            new_progress = Progress(
                user_id=user_id, 
                date=date.today(), 
                workout_completed=workout_completed, 
                slept_well=slept_well
            )
            db.session.add(new_progress)

        db.session.commit()

        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html')



@app.route('/fortschritt', methods=['GET', 'POST'])
@login_required
def fortschritt():
    user_id = current_user.get_id()
    user = User.query.get(user_id)

    if request.method == 'POST':
        
        if 'gewicht' in request.form:
            gewicht = request.form.get('gewicht', type=float)
            user.gewicht = gewicht
        
        elif 'zielgewicht' in request.form:
            zielgewicht = request.form.get('zielgewicht', type=float)
            user.zielgewicht = zielgewicht
        
        db.session.commit()
        return redirect(url_for('fortschritt'))  

    start_date = date.today() - timedelta(days=364)
    progress_data = Progress.query.filter(Progress.user_id == user_id, Progress.date >= start_date).order_by(Progress.date.asc()).all()

    if progress_data:
        slept_well_data = [{'date': p.date.strftime('%Y-%m-%d'), 'value': p.slept_well} for p in progress_data]
        workout_data = [{'date': p.date.strftime('%Y-%m-%d'), 'value': p.workout_completed} for p in progress_data]
    else:
        slept_well_data = [{'date': (date.today() - timedelta(days=i)).strftime('%Y-%m-%d'), 'value': False} for i in range(364, -1, -1)]
        workout_data = [{'date': (date.today() - timedelta(days=i)).strftime('%Y-%m-%d'), 'value': False} for i in range(364, -1, -1)]

    entfernung_zum_ziel = user.zielgewicht - user.gewicht if user.gewicht and user.zielgewicht else None

    return render_template('fortschritt.html', 
                           user=user, 
                           entfernung_zum_ziel=entfernung_zum_ziel, 
                           slept_well_data=slept_well_data, 
                           workout_data=workout_data)





# Anwendungsstartpunkt
if __name__ == '__main__':
    app.run(debug=True)
