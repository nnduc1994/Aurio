from flask import render_template, request, flash, g, session, redirect, url_for, jsonify, abort, make_response
from app import app, db, lm
from models import User, Key, Transaction, Company
from forms import LoginForm, CreateKeyForm, SearchForm, CreateCompanyForm, CreateUserForm, RemoveUserForm
from flask_login import login_user, login_required, logout_user, current_user
import datetime
from datetime import timedelta



@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/intranet/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == "POST":
        if current_user is not None and current_user.is_authenticated():
            return redirect(url_for("main"))
        user = User.query.filter(User.user_name == form.user_name.data).first()

        if user is None:
            flash("Username not found")
            return render_template('log_in.html', form=form)
        if user.check_password(form.password.data) == False:
            flash("Password did not match")
            return render_template('log_in.html', form=form)
        if user.activate == False:
            flash("You have been banned or have no permission to login")
            return render_template('log_in.html', form=form)
        login_user(user, remember=form.remember_me.data)
        session['user_id'] = user.id
        if session.get("next"):
            return redirect(session.get("next"))
        else:
            return redirect(url_for("main"))
    else:
        session['next'] = request.args.get('next')
        return render_template('log_in.html', form=form)


@app.route('/intranet/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/intranet/key_list', methods=['GET', 'POST'])
@app.route('/intranet/key_list/<string:act>/<int:key_id>', methods=['GET', 'POST'])
@login_required
def main(key_id=0, act=""):
    user_obj = User()
    tran_obj = Transaction()
    key_obj = Key()
    search_form = SearchForm()
    keys = user_obj.list_all_key(current_user.role, current_user.company_id)
    if request.method == "POST":
        if act == "take":
            selected_key = key_obj.query.get(key_id)
            selected_key.available = False
            db.session.add(selected_key)
            new_transaction = Transaction(user=current_user, key_id=key_id, time_stamp=datetime.datetime.now() + timedelta(hours=3))
            db.session.add(new_transaction)
            db.session.commit()
            flash("Key Taken")
            return redirect(url_for('main'))
        elif act == "release":
            selected_key = key_obj.query.get(key_id)
            selected_key.available = True
            db.session.add(selected_key)
            db.session.commit()
            flash("Key Release")
            return redirect(url_for('main'))
    if search_form.validate_on_submit():
        print search_form.key_input.data
        string_input = search_form.key_input.data
        if string_input == "":
            flash("Please enter something for searching")
            return redirect(url_for("main"))
        else:
            return redirect(url_for('search', input=string_input))
    elif request.method == "GET":
        return render_template("main.html", keys=keys, search_form=search_form)

@app.route('/intranet/key/<int:id>')
@login_required
def key_info(id):
    key_obj = Key.query.get(id)
    search_form = SearchForm()
    transaction_list = key_obj.get_all_transaction()
    if transaction_list is None:
        transaction_list = []
    return render_template("key_info.html", list=transaction_list, search_form=search_form, key=key_obj)

@app.route('/intranet/profile/<int:id>')
@login_required
def profile(id):
        search_form = SearchForm()
        user_obj = User()
        query_user = user_obj.query.get(id)
        trans_list = query_user.list_all_transaction()
        return render_template("profile.html", list=trans_list, user=query_user, search_form=search_form)

@app.route('/intranet/create_key', methods=['GET', 'POST'])
@login_required
def create_key():
    form = CreateKeyForm()
    search_form = SearchForm()
    company_list = current_user.list_all_company()
    # Remove Aurio Head company from the list
    for company in company_list:
        if company.name == "Aurio Head":
            company_list.remove(company)
    if request.method == "POST":
        key_obj = Key()
        key_obj.key_number = int(form.key_number.data)
        key_obj.available = True
        check_list = key_obj.get_all_key(current_user.company.id)
        if current_user.role == 3:
            key_obj.company_id = int(form.selected_company.data)
        elif current_user.role == 2:
            key_obj.company_id = current_user.company_id

        db.session.add(key_obj)
        db.session.commit()
        flash("Key have been created")

        return render_template("create_key.html", form=form, search_form=search_form, list=company_list)
    else:
        if current_user.role == 1:
            flash("You have no permission")
            return redirect(url_for("main"))
        else:
            return render_template("create_key.html", form=form, search_form=search_form, list=company_list)

@app.route('/intranet', methods=['GET', 'POST'])
@app.route('/intranet/my_key/<string:act>/<int:key_id>', methods=['GET', 'POST'])
@login_required
def my_key(key_id=0, act=""):
    transaction_list = current_user.key_taken_by_me_at_moment()
    key_obj = Key()
    search_form = SearchForm()
    if request.method == "POST":
        if act == "release":
            selected_key = key_obj.query.get(key_id)
            selected_key.available = True
            db.session.add(selected_key)
            db.session.commit()
            flash("Key Release")
            return redirect(url_for('my_key'))
        if act == "all":
            for tran in transaction_list:
                selected_key = tran.key
                selected_key.available = True
                db.session.add(selected_key)
                db.session.commit()
            flash("ALL Keys Release")
            return redirect(url_for('my_key'))
    else:
        return render_template("my_key.html", list=transaction_list, search_form=search_form)

@app.route('/intranet/search/<string:input>', methods=['GET', 'POST'])
@login_required
def search(input=""):
    search_form = SearchForm()
    key_number_list = []
    keys = []
    key_obj = Key()

    if "," in input:
        key_number_list = input.split(",")
        for num in key_number_list:
            key_list = key_obj.get_key_by_key_number(int(num))
            for key in key_list:
                keys.append(key)
    else:
        key = key_obj.get_key_by_key_number(int(input))
        for k in key:
            keys.append(k)

    if request.method == "POST":
        for key in keys:
            if key.available == True:
                selected_key = key_obj.query.get(key.id)
                selected_key.available = False
                db.session.add(selected_key)
                new_transaction = Transaction(user=current_user, key_id=key.id, time_stamp=datetime.datetime.now() + timedelta(hours=3))
                db.session.add(new_transaction)
                db.session.commit()
        flash("ALL keys taken")
        return render_template("result_page.html", keys=keys, search_form=search_form)
    if request.method == "GET":
        return render_template("result_page.html", keys=keys, search_form=search_form)

@app.route("/intranet/key_in_use")
@login_required
def key_in_use():
    search_form = SearchForm()
    user_list = current_user.get_key_in_taken()
    return render_template("key_in_use.html", list=user_list, search_form=search_form)

@app.route("/intranet/create_company", methods=['GET', 'POST'])
@login_required
def create_company():
    search_form = SearchForm()
    form = CreateCompanyForm()
    if request.method == "POST":
        comp_obj = Company()
        comp_obj.name = form.company_name.data
        db.session.add(comp_obj)
        db.session.commit()
        flash("Create company success")
        return render_template("create_company.html", search_form=search_form, form=form)
    else:
        if current_user.role != 3:
            flash("You have no permission")
            return redirect(url_for("main"))
        return render_template("create_company.html", search_form=search_form, form=form)

@app.route("/intranet/company_list")
@login_required
def company_list():
    search_form = SearchForm()
    if current_user.role == 1:
        flash("You have no permission")
        return redirect(url_for("main"))
    elif current_user.role == 2:
        company_list = current_user.list_all_company_by_user()
        return render_template("company_list.html", list=company_list, search_form=search_form)
    elif current_user.role == 3:
        company_list = current_user.list_all_company()
        return render_template("company_list.html", list=company_list, search_form=search_form)

@app.route('/intranet/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    search_form = SearchForm()
    company_list = current_user.list_all_company()

    # Remove Aurio Head company from the list
    for company in company_list:
        if company.name == "Aurio Head":
            company_list.remove(company)

    create_form = CreateUserForm()
    if request.method == "POST":
        user_obj = User()
        user_obj.user_name = create_form.user_name.data
        user_obj.name = create_form.name.data
        user_obj.password = create_form.password.data
        user_obj.hash_password() # Hashing password
        user_obj.role = int(create_form.role.data)
        user_obj.activate = True
        if current_user.role == 3:
            user_obj.company_id = int(create_form.selected_company.data)
        elif current_user.role == 2:
            user_obj.company_id = current_user.company_id

        user_list = user_obj.list_all_exsit_user()
        for user in user_list:
            if user.user_name == user_obj.user_name:
                flash("User_name is duplicate")
                return render_template("create_user.html", search_form=search_form, create_form=create_form, list=company_list)
        db.session.add(user_obj)
        db.session.commit()
        flash("User create success")
        return render_template("create_user.html", search_form=search_form, create_form=create_form, list=company_list)
    elif request.method == "GET":
        if current_user.role == 1:
            flash("You have no permission")
            return redirect(url_for("main"))
        else:
            return render_template("create_user.html", search_form=search_form, create_form=create_form, list=company_list)

@app.route('/intranet/remove_user', methods=['GET', 'POST'])
@login_required
def remove_user():
    search_form = SearchForm()
    remove_form = RemoveUserForm()
    user_list = current_user.list_all_user_by_company()

    if request.method == "POST":
        user_object = User()
        query_user = user_object.query.get(int(remove_form.selected_user.data))
        query_user.activate = False
        db.session.add(query_user)
        db.session.commit()
        flash("User Remove/ Banned success")
        return redirect(url_for('remove_user'))


    elif request.method == "GET":
        if current_user.role == 1:
            flash("You have no permission")
            return redirect(url_for("main"))
        else:
            return render_template("remove_user.html", search_form=search_form, user_list=user_list, remove_form=remove_form)


@app.route('/intranet/control_panel/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_control_panel(user_id):
    user_obj = User()
    create_form = CreateUserForm()
    search_form = SearchForm()
    query_user = user_obj.query.get(user_id)
    if request.method == "POST":
        query_user.name = create_form.name.data
        print(create_form.role.data)

        if create_form.password.data == "":
            query_user.password = query_user.password
        else:
            query_user.password = create_form.password.data
            query_user.hash_password()
        if query_user.role == 3:
            query_user.role = 3
        else:
            if create_form.role.data != 'None':
                query_user.role = int(create_form.role.data)
            else:
                query_user.role = query_user.role
        db.session.add(query_user)
        db.session.commit()
        flash("User Info Updated")
        return redirect(url_for("main"))
    elif request.method == "GET":
        if current_user.id != user_id:
            if current_user.role == 1:
                flash("You have no permission")
                return redirect(url_for("main"))
            elif current_user.company_id == query_user.company_id and current_user.role == 2:
                return render_template('user_control_panel.html', user=query_user, search_form=search_form,
                                       create_form=create_form)
            elif current_user.role == 3:
                return render_template('user_control_panel.html', user=query_user, search_form=search_form,
                                       create_form=create_form)
        return render_template('user_control_panel.html', user=query_user, search_form=search_form,
                               create_form=create_form)


@app.route('/intranet/remove_key', methods=['GET', 'POST'])
@app.route('/intranet/remove_key/<int:key_id>', methods=['GET', 'POST'])
@login_required
def remove_key(key_id=0):
    search_form = SearchForm()
    if request.method == "POST":
        query_key = Key.query.get(key_id)
        transaction_list = Transaction.query.filter(Transaction.key_id == key_id).all()
        for tran in transaction_list:
            db.session.delete(tran)
        db.session.delete(query_key)
        db.session.commit()
        flash("Remove Key Successful")
        return redirect(url_for('remove_key'))
    else:
        user_obj = User()
        key_list = user_obj.list_all_key(current_user.role, current_user.company_id)
        key_list_complete = []
        for key in key_list:
            key.company_name = Company.query.get(key.company_id).name
            key_list_complete.append(key)
        return render_template("remove_key.html", search_form=search_form, list=key_list_complete)



######### API ##################

# allow CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'User not found'}), 400)

@app.route("/intranet/api/login/<string:username>/<string:password>", methods=['GET'])
def log_in_api(username, password):

    query_user = User.query.filter(User.user_name == username).first()
    if query_user is None:
        return make_response(jsonify({'error': 'User not found'}))
    if query_user.check_password(password) == False:
        return make_response(jsonify({'error': 'User not found'}))
    serialize_user = query_user.serialize()
    return jsonify({'user': serialize_user})


@app.route("/intranet/api/get_all_key/<string:userId>")
def api_get_all_key(userId):
    userId_string = int(userId)
    user_obj = User.query.get(userId_string)
    keys = user_obj.list_all_key(1, user_obj.company_id).all()
    serialize_key_list = []
    for key in keys:
        last_transaction = key.get_latest_transaction()
        if last_transaction is not None:
            key.last_transaction_name = User.query.get(last_transaction.user_id).name
            key.last_transaction_time = last_transaction.time_stamp.strftime("%d.%m.%y - %H:%M")
        else:
            key.last_transaction_name = None
            key.last_transaction_time = None
        serialize_key = key.serialize()
        serialize_key_list.append(serialize_key)

    return jsonify({'keys': serialize_key_list})

