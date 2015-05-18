from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    users = db.relationship("User", backref="company", lazy="dynamic")
    keys = db.relationship("Key", backref="company", lazy="dynamic")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"))
    name = db.Column(db.String(150))
    user_name = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))
    role = db.Column(db.Integer)
    activate = db.Column(db.Boolean)
    transaction = db.relationship("Transaction", backref="user", lazy="dynamic")

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.activate

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def list_all_key(self, role, company_id):
        if role == 1 or role == 2:
            return Key.query.join(User, (Key.company_id == company_id)).order_by(Key.key_number.asc())
        elif role == 3:
            return Key.query.order_by(Key.key_number.asc())

    def list_all_transaction(self):
        return Transaction.query.join(User, (Transaction.user_id == self.id)).order_by(Transaction.time_stamp.desc()).all()

    def key_taken_by_me_at_moment(self):
        if self.role != 3:
            unavailable_keys = Key.query.filter(Key.available == False, Key.company_id == self.company_id)
        else:
            unavailable_keys = Key.query.filter(Key.available == False)
        key_transaction_taken_list = []
        for key in unavailable_keys:
            latest_tran = key.get_latest_transaction()
            if latest_tran.user_id == self.id:
                key_transaction_taken_list.append(latest_tran)
        return key_transaction_taken_list

    def get_key_in_taken(self):
        if self.role == 1 or self.role == 2:
            unavailable_keys = Key.query.filter(Key.available == False, Key.company_id == self.company_id)
            all_user = User.query.filter(User.company_id == self.company_id).all()
        elif self.role == 3:
            unavailable_keys = Key.query.filter(Key.available == False)
            all_user = User.query.all()

        for user in all_user:
            user.key_taken_list = []
        for key in unavailable_keys:
            latest_tran = key.get_latest_transaction()
            for user in all_user:
                if user.id == latest_tran.user_id:
                    user.key_taken_list.append(key)
        return all_user

    def list_all_company(self):
        company_list = Company.query.all()
        for company in company_list:
            company.user_list = []
            user = User.query.filter(User.company_id == company.id).all()
            for u in user:
                company.user_list.append(u)
        return company_list

    def list_all_company_by_user(self): # Using for list company html file
        company_list = Company.query.filter(Company.id == self.company_id).all()
        for company in company_list:
            company.user_list = []
            user = User.query.filter(User.company_id == company.id).all()
            for u in user:
                company.user_list.append(u)
        return company_list

    def list_all_exsit_user(self):
        return User.query.filter(User.activate == True).all()

    def list_all_user_by_company(self): # for remove user purpose
        if self.role == 2:
            return User.query.filter(User.activate == True, User.company_id == self.company_id, User.id != self.id,
                                 User.role != 3).all()
        elif self.role == 3:
            return User.query.filter(User.activate == True, User.id != self.id)

    def get_company_by_user(self): # for remove user purpose
        return Company.query.filter(Company.id == self.company_id).first()

    def hash_password(self):
        self.password = generate_password_hash(self.password)

    def check_password(self, input_password):
        hash_input_password = generate_password_hash(input_password)
        return check_password_hash(hash_input_password, self.password)

    # API function #
    def serialize(self):
        return {
            'id': self.id,
            'companyId': self.company_id,
            'name': self.name,
            'role': self.role,
            'activate': self.activate
        }

class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"))
    key_number = db.Column(db.Integer)
    available = db.Column(db.Boolean)
    transaction = db.relationship("Transaction", backref="key", lazy="dynamic")

    def get_latest_transaction(self):
        trans = Transaction.query.join(Key, (Transaction.key_id == self.id)).order_by(Transaction.time_stamp.desc()).first()
        if trans is not None:
            return trans

    def get_all_transaction(self):
        trans = Transaction.query.join(Key, (Transaction.key_id == self.id)).order_by(Transaction.time_stamp.desc()).all()
        if trans is not None:
            return trans

    def get_all_key(self, companyId):
        key_list = Key.query.filter(Key.company_id == companyId).all()
        if key_list is not None:
            return key_list

    def get_key_by_key_number(self, key_number):
        key = Key.query.filter(Key.key_number == key_number).first()
        if key is not None:
            return key

    # API function #
    def serialize(self):
        return {
            'id': self.id,
            'companyId': self.company_id,
            'key_number': self.key_number,
            'available': self.available,
            'last_transaction_name': self.last_transaction_name,
            'last_transaction_time': self.last_transaction_time
        }


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    key_id = db.Column(db.Integer, db.ForeignKey("key.id"))
    time_stamp = db.Column(db.DateTime)